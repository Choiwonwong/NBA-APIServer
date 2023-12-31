import boto3
from botocore.exceptions import NoCredentialsError
import re

fixedQuest = "[변경 불가]-"

def preProcess(obj):
    if isinstance(obj, dict):
        return {str(key).replace("_", ""): preProcess(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [preProcess(item) for item in obj]
    else:
        return str(obj)
    
def is_english(text): 
    english_pattern = re.compile(r'^[0-9a-zA-Z\s\-_]*$')
    return bool(english_pattern.match(text))
    
def get_nested_value(data, path):
    keys = path.split('.')
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return None
    return data

class ProcessController:
    def __init__(self, quest: dict):
        self.quest = quest
    
    def processQuestU(self):
        userQuestYaml = {
            "요청_명": self.quest.get("요청명"),
            "요청_타입": self.quest.get("요청타입", "전체"),
            "AWS_지역_명": self.quest.get("AWS인증정보", {}).get("AWS지역명", "도쿄"),
            "네트워크_환경": {
                "개인_작업_네트워크_이름(VPC)": self.quest.get("네트워크환경", {}).get("개인작업네트워크이름", "quest-vpc").lower(),
                "인터넷_가능_블럭_네트워크(Public_Subnet)": self.quest.get("네트워크환경", {}).get("인터넷가능블럭네트워크", "2") + "개",
                "인터넷_불가능_블럭_네트워크(Private_Subnet)": self.quest.get("네트워크환경", {}).get("인터넷불가능블럭네트워크", "2") + "개",
                "인터넷_게이트웨이(IGW)": self.quest.get("네트워크환경", {}).get("인터넷게이트웨이", "1") + "개",
                "인터넷주소_변환_게이트웨이(NAT_GW)": self.quest.get("네트워크환경", {}).get("인터넷주소변환게이트웨이", "1") + "개",
            },
            "컴퓨팅_요청": {
                "컨트롤_플레인(EKS)": {
                    "이름": self.quest.get("컴퓨팅요청", {}).get("컨트롤플레인", {}).get("이름", "quest-eks").lower(),
                    "버전": self.quest.get("컴퓨팅요청", {}).get("컨트롤플레인", {}).get("버전", "1.27"),
                },
                "데이터_플레인": {
                    "이름": self.quest.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("이름", "quest-data-plane").lower(),
                    "기반": fixedQuest+ "가상머신",
                    "과금방식": fixedQuest + "SPOT",
                    "스펙": None,
                    "가상머신_개수": {
                        "최대": self.quest.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("가상머신개수", {}).get("최대", "4") + "개",
                        "최소": self.quest.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("가상머신개수", {}).get("최소", "2") + "개",
                        "요구": self.quest.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("가상머신개수", {}).get("요구", "3") + "개",
                    }
                }
            },
            "배포_요청": {
                "네임_스페이스_이름": self.quest.get("배포요청", {}).get("네임스페이스이름", "default").lower(),
                "애플리케이션":{
                    "앱_이름": self.quest.get("배포요청", {}).get("애플리케이션", {}).get("이름", "quest-app").lower(),
                    "이미지_이름": self.quest.get("배포요청", {}).get("애플리케이션", {}).get("이미지이름"),
                    "포트_번호": self.quest.get("배포요청", {}).get("애플리케이션", {}).get("포트번호"),
                    "복제본_개수": self.quest.get("배포요청", {}).get("애플리케이션", {}).get("복제본개수", "3"),
                },
                "서비스": {
                    "서비스_이름": self.quest.get("배포요청", {}).get("서비스", {}).get("이름", "quest-service").lower(),
                    "서비스_타입": fixedQuest+ "로드밸런서",
                },
                "환경_변수": [],
            }
        }

        spec = self.quest.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("스펙", "중")
        spec_Dict = {
            "대": "t3.large",
            "중": "t3.medium",
        }
        userQuestYaml["컴퓨팅_요청"]["데이터_플레인"]["스펙"] = spec + f"({spec_Dict.get(spec)})"

        # 배포 환경변수 처리
        env_list = self.quest.get("배포요청", {}).get("환경변수")
        if env_list:
            if isinstance(env_list, list):
                for item in env_list:
                    if isinstance(item, dict):
                        env_entry = {
                            "환경_변수_명": item.get("이름"),
                            "환경_변수_값": item.get("값")
                        }
                        userQuestYaml["배포_요청"]["환경_변수"].append(env_entry)
            elif isinstance(env_list, dict):
                env_entry = {
                    "환경_변수_명": env_list.get("이름"),
                    "환경_변수_값": item.get("값")
                }
                userQuestYaml["배포_요청"]["환경_변수"].append(env_entry)
        else:
            del userQuestYaml["배포_요청"]["환경_변수"]
        
        # 서비스 요청 타입에 따라 처리
        if userQuestYaml["요청_타입"] != "배포":
            processedQuest = {
                "요청_명": userQuestYaml.get('요청_명', ''),
                "요청_타입": userQuestYaml.get('요청_타입', ''),
                "AWS_지역_명": userQuestYaml.get('AWS_지역_명', ''),
                '네트워크_환경': userQuestYaml.get('네트워크_환경', {}),
                '컴퓨팅_요청': userQuestYaml.get('컴퓨팅_요청', {}),
                '배포_요청': userQuestYaml.get('배포_요청', {}),
            }
        else:
            processedQuest = {
                "요청_명": userQuestYaml.get('요청_명', ''),
                "요청_타입": userQuestYaml.get('요청_타입', ''),   
                "AWS_지역_명": userQuestYaml.get('AWS_지역_명', ''),
                '기존_컴퓨팅_환경': {
                    "컨트롤_플레인": userQuestYaml.get("컴퓨팅_요청", {}).get("컨트롤_플레인(EKS)", {}).get("이름"),
                    "데이터_플레인": userQuestYaml.get("컴퓨팅_요청", {}).get("데이터_플레인", {}).get("이름"),
                },
                '배포_요청': userQuestYaml.get('배포_요청', ''),
                
            }            
            # processedQuest["기존_컴퓨팅_환경"]["컨트롤_플레인"]["이름"] = self.quest.get("컴퓨팅요청", {}).get("컨트롤플레인", {}).get("이름", "quest-eks").lower()
            # processedQuest["기존_컴퓨팅_환경"]["데이터_플레인"]["이름"] = self.quest.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("이름", "quest-data-plane").lower()
        return processedQuest
    
    def checkAWSCredential(self):
        if self.quest.get("AWS인증정보").get("AWS계정접근키") == "" or self.quest.get("AWS인증정보").get("AWS계정비밀키") == "": 
            print("AWS Credential is not valid.")
            return False        
        try:
            client = boto3.client('iam', 
                                  aws_access_key_id=self.quest.get("AWS인증정보").get("AWS계정접근키"), 
                                  aws_secret_access_key=self.quest.get("AWS인증정보").get("AWS계정비밀키"),
                                  )
            response = client.get_user()
            user_name = response['User']['Arn'].split(':')[-1]
            if user_name == 'root':
                return True 
            print(f"AWS Credential belongs to user: {user_name}, but it is not the root user.")
            return False
        except NoCredentialsError:
            print("AWS Credential is not valid.")
            return False
        except Exception as e:
            print(f"An error occurred while checking AWS Credential: {str(e)}")
            return False
        
    def processQuestC(self):
        result = {}
        result['requestTitle'] = self.quest.get("요청명")
        result['requestType'] = self.quest.get("요청타입", "전체")
        result['awsAccessKey'] = self.quest.get("AWS인증정보").get("AWS계정접근키")
        result['awsSecretKey'] = self.quest.get("AWS인증정보").get("AWS계정비밀키")
        result['clusterName'] = self.quest.get("컴퓨팅요청", {}).get("컨트롤플레인", {}).get("이름", "quest-eks").lower()
        result['dataPlaneName'] = self.quest.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("이름", "quest-data-plane").lower()
        result['namespaceName'] = self.quest.get("배포요청", {}).get("네임스페이스이름", "default").lower()
        result['deploymentName'] = self.quest.get("배포요청", {}).get("애플리케이션", {}).get("이름", "quest-app").lower()
        result['serviceName'] = self.quest.get("배포요청", {}).get("서비스", {}).get("이름", "quest-service").lower()
        
        if "서울" in self.quest.get("AWS인증정보").get("AWS지역명", "도쿄"):
            result['awsRegionName'] = "ap-northeast-2"
        else:
            result['awsRegionName'] = "ap-northeast-1"
        return result
    
    def processQuestI(self):
        processedQuest = {}
        processedQuest['provision'] = {}
        processedQuest['deploy'] = {}

        processedQuest['provision']['TITLE'] = self.quest.get("요청명")
        processedQuest["provision"]["AWS_EKS_NAME"] = self.quest.get("컴퓨팅요청", {}).get("컨트롤플레인", {}).get("이름", "quest-eks").lower()
        processedQuest["provision"]["EKS_VER"] = str(self.quest.get("컴퓨팅요청", {}).get("컨트롤플레인", {}).get("버전", 1.27))
        processedQuest["provision"]['AWS_DATAPLANE_NAME'] = self.quest.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("이름", "quest-data-plane").lower()
        processedQuest["provision"]['CAPACITY_TYPE'] = "SPOT"
        processedQuest["provision"]["PUB_SUB_COUNT"] = str(self.quest.get("네트워크환경", {}).get("인터넷가능블럭네트워크", 2))
        processedQuest["provision"]["PRI_SUB_COUNT"] = str(self.quest.get("네트워크환경", {}).get("인터넷불가능블럭네트워크", 2))
        processedQuest["provision"]['SCALING_MAX'] = str(self.quest.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("가상머신개수", {}).get("최대", 4))
        processedQuest["provision"]['SCALING_MIN'] = str(self.quest.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("가상머신개수", {}).get("최소", 2))
        processedQuest["provision"]['SCALING_DESIRE'] = str(self.quest.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("가상머신개수", {}).get("요구", 3))
        processedQuest["provision"]['DL'] = "$"
        processedQuest["provision"]['LB_EOF'] = "EOF"
        processedQuest["provision"]['VPC_NAME'] = str(self.quest.get("네트워크환경", {}).get("개인작업네트워크이름", "quest-vpc")).lower()

        spec_list = {
            "대": "t3.large",
            "중": "t3.medium",
        }
        spec = self.quest.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("스펙", "중")
        processedQuest["provision"]['INSTANCE_TYPE'] = spec_list.get(spec)

        processedQuest["deploy"]["AWS_EKS_NAME"] = self.quest.get("컴퓨팅요청", {}).get("컨트롤플레인", {}).get("이름", "quest-eks").lower()
        processedQuest["deploy"]["TITLE"] = self.quest.get("요청명")
        processedQuest["deploy"]["NAMESPACE_NAME"] = self.quest.get("배포요청", {}).get("네임스페이스이름", "default").lower()
        processedQuest["deploy"]["DEPLOY_NAME"] = self.quest.get("배포요청", {}).get("애플리케이션", {}).get("이름", "quest-app").lower()
        processedQuest["deploy"]["DEPLOY_REPLICAS"] = str(self.quest.get("배포요청", {}).get("애플리케이션", {}).get("복제본개수", 3))
        processedQuest["deploy"]["DEPLOY_CONTAINER_IMAGE"] = self.quest.get("배포요청", {}).get("애플리케이션", {}).get("이미지이름")
        processedQuest["deploy"]["PORT"] = str(self.quest.get("배포요청", {}).get("애플리케이션", {}).get("포트번호"))
        processedQuest["deploy"]["SVC_NAME"] = self.quest.get("배포요청", {}).get("서비스", {}).get("이름", "quest-service").lower()

        secrets = self.quest.get("배포요청", {}).get("환경변수", {})
        if secrets:
            tmp = []
            for secret in secrets:
                tmp.append({"key": secret.get("이름"), "value": secret.get("값")})
                processedQuest["deploy"]["SECRET"] = str(tmp)
        if self.quest.get("요청타입", "전체") ==  "배포":
            del processedQuest["provision"]
        return processedQuest
    

    # security_groups = self.quest.get("컴퓨팅요청", {}).get("컨트롤플레인", {}).get("방화벽", {})
        # if security_groups:
        #     firewall_rules = []
        #     for rule in security_groups:
        #         firewall_rule = {
        #                 "from_port": rule.get("허용포트"),
        #                 "to_port": rule.get("허용포트"),
        #                 "protocol": "tcp",
        #                 "cidr_blocks": [rule.get("허용대역")]
        #             }    
        #         firewall_rules.append(firewall_rule)
        #     processedQuest["provision"]["TF_VAR_SECURITY_GROUP_INGRESS"] = str(firewall_rules)
    
    # 방화벽 처리
        # firewall_item = self.quest.get("컴퓨팅요청", {}).get("컨트롤플레인", {}).get("방화벽")
        # if firewall_item:
        #     if isinstance(firewall_item, list):
        #         for item in firewall_item:
        #             if isinstance(item, dict):
        #                 허용_포트 = item.get("허용포트", 8000)
        #                 허용_대역 = item.get("허용대역", "0.0.0.0/0")
        #                 firewall_entry = {
        #                     "허용_포트": 허용_포트,
        #                     "허용_대역": 허용_대역,
        #                 }
        #                 userQuestYaml["컴퓨팅_요청"]["컨트롤_플레인(EKS)"]["방화벽"].append(firewall_entry)
        #     elif isinstance(firewall_item, dict):
        #         허용_포트 = firewall_item.get("허용포트", 8000)
        #         허용_대역 = firewall_item.get("허용대역", "0.0.0.0/0")
        #         firewall_entry = {
        #             "허용_포트": 허용_포트,
        #             "허용_대역": 허용_대역,
        #         }
        #         userQuestYaml["컴퓨팅_요청"]["컨트롤_플레인(EKS)"]["방화벽"].append(firewall_entry)
        # else:
        #     del userQuestYaml["컴퓨팅_요청"]["컨트롤_플레인(EKS)"]["방화벽"]