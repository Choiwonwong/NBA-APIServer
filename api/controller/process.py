import boto3
from botocore.exceptions import NoCredentialsError

fixedQuest = "[변경 불가]-"

def preProcess(obj):
    if isinstance(obj, dict):
        return {str(key).replace("_", ""): preProcess(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [preProcess(item) for item in obj]
    else:
        return str(obj)
    
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
            "AWS_지역_명": self.quest.get("배포_지역_명", "도쿄"),
            "네트워크_요청": {
                "개인_작업_네트워크_공간(VPC)": self.quest.get("네트워크요청", {}).get("개인작업네트워크공간", "1") + "개",
                "인터넷_가능_블럭_네트워크(Public_Subnet)": self.quest.get("네트워크요청", {}).get("인터넷가능블럭네트워크", "2") + "개",
                "인터넷_불가능_블럭_네트워크(Private_Subnet)": self.quest.get("네트워크요청", {}).get("인터넷불가능블럭네트워크", "2") + "개",
                "인터넷_게이트웨이(IGW)": self.quest.get("네트워크요청", {}).get("인터넷게이트웨이", "1") + "개",
                "인터넷주소_변환_게이트웨이(NAT_GW)": self.quest.get("네트워크요청", {}).get("인터넷주소변환게이트웨이", "1") + "개",
            },
            "컴퓨팅_요청": {
                "컨트롤_플레인(EKS)": {
                    "이름": self.quest.get("컴퓨팅요청", {}).get("컨트롤플레인", {}).get("이름", "quest-eks"),
                    "버전": self.quest.get("컴퓨팅요청", {}).get("컨트롤플레인", {}).get("버전", "1.27"),     
                    "방화벽": [],
                },
                "데이터_플레인": {
                    "이름": self.quest.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("이름", "quest-data-plane"),
                    "기반": fixedQuest+ "가상머신",
                    "스펙": self.quest.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("스펙", "t3.medium"),
                    "과금방식": fixedQuest + "SPOT",
                    "가상머신_개수": {
                        "최대": self.quest.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("가상머신개수", {}).get("최대", "4") + "개",
                        "최소": self.quest.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("가상머신개수", {}).get("최소", "2") + "개",
                        "요구": self.quest.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("가상머신개수", {}).get("요구", "3") + "개",
                    }
                }
            },
            "배포_요청": {
                "네임_스페이스_이름": self.quest.get("배포요청", {}).get("네임스페이스이름", "default"),
                "애플리케이션":{
                    "앱_이름": self.quest.get("배포요청", {}).get("애플리케이션", {}).get("앱이름", 'quest-app'),
                    "이미지_이름": self.quest.get("배포요청", {}).get("애플리케이션", {}).get("이미지이름"),
                    "포트_번호": self.quest.get("배포요청", {}).get("애플리케이션", {}).get("포트번호"),
                    "복제본_개수": self.quest.get("배포요청", {}).get("애플리케이션", {}).get("복제본개수", "3"),
                },
                "서비스": {
                    "서비스_이름": self.quest.get("배포요청", {}).get("서비스", {}).get("서비스이름", "quest-service"),
                    "서비스_타입": fixedQuest+ "로드밸런서",
                },
                "환경_변수": [],
            }
        }

        # 방화벽 처리
        firewall_item = self.quest.get("컴퓨팅요청", {}).get("컨트롤플레인", {}).get("방화벽")
        if firewall_item:
            if isinstance(firewall_item, list):
                for item in firewall_item:
                    if isinstance(item, dict):
                        허용_포트 = item.get("허용포트", 8000)
                        허용_대역 = item.get("허용대역", "0.0.0.0/0")
                        firewall_entry = {
                            "허용_포트": 허용_포트,
                            "허용_대역": 허용_대역,
                        }
                        userQuestYaml["컴퓨팅_요청"]["컨트롤_플레인(EKS)"]["방화벽"].append(firewall_entry)
            elif isinstance(firewall_item, dict):
                허용_포트 = firewall_item.get("허용포트", 8000)
                허용_대역 = firewall_item.get("허용대역", "0.0.0.0/0")
                firewall_entry = {
                    "허용_포트": 허용_포트,
                    "허용_대역": 허용_대역,
                }
                userQuestYaml["컴퓨팅_요청"]["컨트롤_플레인(EKS)"]["방화벽"].append(firewall_entry)
        else:
            del userQuestYaml["컴퓨팅_요청"]["컨트롤_플레인(EKS)"]["방화벽"]
        # 배포 환경변수 처리
        env_list = self.quest.get("배포요청", {}).get("환경변수")
        if env_list:
            if isinstance(env_list, list):
                for item in env_list:
                    if isinstance(item, dict):
                        env_entry = {
                            "환경_변수_명": item.get("이름"),
                        }
                        userQuestYaml["배포_요청"]["환경_변수"].append(env_entry)
            elif isinstance(env_list, dict):
                env_entry = {
                    "환경_변수_명": env_list.get("이름"),
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
                '네트워크_요청': userQuestYaml.get('네트워크_요청', {}),
                '컴퓨팅_요청': userQuestYaml.get('컴퓨팅_요청', {}),
                '배포_요청': userQuestYaml.get('배포_요청', {}),
            }
        else:
            processedQuest = {
                "요청_명": userQuestYaml.get('요청_명', ''),
                "요청_타입": userQuestYaml.get('요청_타입', ''),   
                "AWS_지역_명": userQuestYaml.get('AWS_지역_명', ''),
                '기존_컴퓨팅_환경': {
                    "컨트롤_플레인": {},
                    "데이터_플레인": {},
                },
                '배포_요청': userQuestYaml.get('배포_요청', ''),
                
            }            
            processedQuest["기존_컴퓨팅_환경"]["컨트롤_플레인"]["이름"] = userQuestYaml.get("컴퓨팅_요청", {}).get("컨트롤_플레인", {}).get("이름", "quest-eks")
            processedQuest["기존_컴퓨팅_환경"]["데이터_플레인"]["이름"] = userQuestYaml.get("컴퓨팅_요청", {}).get("데이터_플레인", {}).get("이름", "quest-data-plane")

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
        result['clusterName'] = self.quest.get("컴퓨팅요청", {}).get("컨트롤플레인", {}).get("이름", "quest-eks")
        result['dataPlaneName'] = self.quest.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("이름", "quest-data-plane")
        result['namespaceName'] = self.quest.get("배포요청", {}).get("네임스페이스이름", "default")
        result['deploymentName'] = self.quest.get("배포요청", {}).get("애플리케이션", {}).get("앱이름", "quest-app")
        result['serviceName'] = self.quest.get("배포요청", {}).get("서비스", {}).get("서비스이름", "quest-service")
        
        if "서울" in self.quest.get("배포_지역_명", "도쿄"):
            result['awsRegionName'] = "ap-northeast-2"
        else:
            result['awsRegionName'] = "ap-northeast-1"
        return result
    
    def processQuestI(self):
        processedQuest = {}
        processedQuest['metadata'] = {}
        processedQuest['provision'] = {}
        processedQuest['deploy'] = {}
        return processedQuest