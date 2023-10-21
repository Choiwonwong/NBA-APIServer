import boto3
from botocore.exceptions import NoCredentialsError

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
    def __init__(self, quest: dict, access_key: str, secret_key: str, title: str):
        self.quest = quest
        self.access_key = access_key
        self.secret_key = secret_key
        self.title = title
    
    def processQuestU(self):
        userQuestYaml = {
            "요청_명": self.quest.get("요청명"),
            "네트워크_요청": {
                "개인_작업_네트워크_공간(VPC)": self.quest.get("네트워크요청", {}).get("개인작업네트워크공간", "1") + "개",
                "인터넷_가능_블럭_네트워크(Public_Subnet)": self.quest.get("네트워크요청", {}).get("인터넷가능블럭네트워크", "2") + "개",
                "인터넷_불가능_블럭_네트워크(Private_Subnet)": self.quest.get("네트워크요청", {}).get("인터넷불가능블럭네트워크", "2") + "개",
                "인터넷_게이트웨이(IGW)": self.quest.get("네트워크요청", {}).get("인터넷게이트웨이", "1") + "개",
                "인터넷주소_변환_게이트웨이(NAT_GW)": self.quest.get("네트워크요청", {}).get("인터넷주소변환게이트웨이", "1") + "개",
            },
            "컴퓨팅_요청": {
                "마스터노드": {
                    "이름": self.quest.get("컴퓨팅요청", {}).get("마스터노드", {}).get("이름", "quest-eks"),
                    "버전": self.quest.get("컴퓨팅요청", {}).get("마스터노드", {}).get("버전", "1.27"),     
                    "방화벽": [],
                },
                "워커노드": {
                    "이름": self.quest.get("컴퓨팅요청", {}).get("워커노드", {}).get("이름", "quest-data-plane"),
                    "기반": self.quest.get("컴퓨팅요청", {}).get("워커노드", {}).get("기반", "가상머신") + "_기반",
                    "스펙": self.quest.get("컴퓨팅요청", {}).get("워커노드", {}).get("스펙", "t3.medium"),
                    "과금_방식": self.quest.get("컴퓨팅요청", {}).get("워커노드", {}).get("과금방식", "SPOT"),
                    "워커노드_개수": {
                        "최대": self.quest.get("컴퓨팅요청", {}).get("워커노드", {}).get("워커노드개수", {}).get("최대", "4") + "개",
                        "최소": self.quest.get("컴퓨팅요청", {}).get("워커노드", {}).get("워커노드개수", {}).get("최소", "2") + "개",
                        "요구": self.quest.get("컴퓨팅요청", {}).get("워커노드", {}).get("워커노드개수", {}).get("요구", "3") + "개",
                    }
                }
            },
            "배포_요청": {
                "네임_스페이스_이름": self.quest.get("배포요청", {}).get("네임스페이스이름"),
                "애플리케이션":{
                    "앱_이름": self.quest.get("배포요청", {}).get("애플리케이션", {}).get("앱이름", 'quest-app'),
                    "이미지_이름": self.quest.get("배포요청", {}).get("애플리케이션", {}).get("이미지이름"),
                    "포트_번호": self.quest.get("배포요청", {}).get("애플리케이션", {}).get("포트_번호"),
                    "복제본_개수": self.quest.get("배포요청", {}).get("애플리케이션", {}).get("복제본개수", "3"),
                },
                "서비스": {
                    "서비스_이름": self.quest.get("배포요청", {}).get("배포", {}).get("서비스이름", "quest-service"),
                    "서비스_타입": self.quest.get("배포요청", {}).get("배포", {}).get("서비스타입", "로드밸런서"),                    
                },
                "환경_변수": [],
            }
        }
        firewall_item = self.quest.get("컴퓨팅요청", {}).get("마스터노드", {}).get("방화벽")
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
                        userQuestYaml["컴퓨팅_요청"]["마스터노드"]["방화벽"].append(firewall_entry)
            elif isinstance(firewall_item, dict):
                허용_포트 = firewall_item.get("허용포트", 8000)
                허용_대역 = firewall_item.get("허용대역", "0.0.0.0/0")
                firewall_entry = {
                    "허용_포트": 허용_포트,
                    "허용_대역": 허용_대역,
                }
                userQuestYaml["컴퓨팅_요청"]["마스터노드"]["방화벽"].append(firewall_entry)
        else:
            del userQuestYaml["컴퓨팅_요청"]["마스터노드"]["방화벽"]

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

        return userQuestYaml
    
    def processQuestI(self):
        processedQuest = {}
        processedQuest['metadata'] = {}
        processedQuest['provision'] = {}
        processedQuest['deploy'] = {}

        try:
            processedQuest['metadata']['TITLE'] = self.title
            # processedQuest['metadata']['namespace'] = self.quest.get('namespace', '')
            processedQuest['metadata']['REGION'] = self.quest.get('배포_지역_명', 'ap-northeast-2')
        except Exception as e:
            raise Exception(f"An error occurred while processing metadata: {str(e)}")

        processedQuest['provision']['CLSSTER_NAME'] = self.quest.get('클러스터_명', f"eks-{self.title}")
        processedQuest['provision']['CIDR'] = self.quest.get('네트워크_영역', '10.0.0.0/16')
        processedQuest['provision']['PUBLIC_SN_COUNT'] = self.quest.get('인터넷_영역_수', '2')
        processedQuest['provision']['PRIVATE_SN_COUNT'] = self.quest.get('보안_영역_수', '2')
    
        # processedQuest['deploy']['cluster_name'] = processedQuest['provision']['cluster_name']
        # processedQuest['deploy']['image_name'] = self.quest.get('앱_이미지', 'nginx:latest')
        # processedQuest['deploy']['port'] = self.quest.get('앱_포트', 80)
        # processedQuest['deploy']['service_type'] = self.quest.get('앱_노출_방식', 'LoadBalancer')
        # processedQuest['deploy']['replicas'] = self.quest.get('앱_복제_수', 1)
        # processedQuest['deploy']['cpu'] = self.quest.get('앱_CPU_스펙', '0.5')
        # processedQuest['deploy']['memory'] = self.quest.get('앱_메모리_스펙', '512MiB')

        return processedQuest
    
    def checkAWSCredential(self):
        if self.access_key == "" or self.secret_key == "":
            print("AWS Credential is not valid.")
            return False
        try:
            client = boto3.client('iam', aws_access_key_id=self.access_key, aws_secret_access_key=self.secret_key)
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