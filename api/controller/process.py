import yaml, json, boto3
from botocore.exceptions import NoCredentialsError

class ProcessController:
    def __init__(self, quest: dict, access_key: str, secret_key: str, title: str):
        self.quest = quest
        self.access_key = access_key
        self.secret_key = secret_key
        self.title = title
    
    def processQuest(self):
        processedQuest = {}
        processedQuest['metadata'] = {""}
        processedQuest['provision'] = {""}
        processedQuest['deploy'] = {""}

        try:
            processedQuest['metadata']['title'] = self.title
            # processedQuest['metadata']['namespace'] = self.quest.get('namespace', '')
            processedQuest['metadata']['region'] = self.quest.get('배포_지역_명', 'ap-northeast-2')
            processedQuest['metadata']['access_key'] = self.access_key
            processedQuest['metadata']['secret_key'] = self.secret_key
        except Exception as e:
            raise Exception(f"An error occurred while processing metadata: {str(e)}")

        processedQuest['provision']['cluster_name'] = self.quest.get('클러스터_명', f"eks-{self.title}")
        processedQuest['provision']['cidr'] = self.quest.get('네트워크_영역', '10.0.0.0/16')
        processedQuest['provision']['public_subnet_count'] = self.quest.get('인터넷_영역_수', 2)
        processedQuest['provision']['private_subnet_count'] = self.quest.get('보안_영역_수', 2)
    

        processedQuest['deploy']['cluster_name'] = processedQuest['provision']['cluster_name']
        processedQuest['deploy']['image_name'] = self.quest.get('앱_이미지', 'nginx:latest')
        processedQuest['deploy']['port'] = self.quest.get('앱_포트', 80)
        processedQuest['deploy']['service_type'] = self.quest.get('앱_노출_방식', 'LoadBalancer')
        processedQuest['deploy']['replicas'] = self.quest.get('앱_복제_수', 1)
        processedQuest['deploy']['cpu'] = self.quest.get('앱_CPU_스펙', '0.5')
        processedQuest['deploy']['memory'] = self.quest.get('앱_메모리_스펙', '512MiB')

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
        

    # def createNamespace(self, namespace):
    #     v1 = self.coreV1client
    #     body = {
    #         'metadata': {
    #             'name': namespace
    #         }
    #     }
    #     try:
    #         v1.create_namespace(body=body)
    #         print(f"Namespace '{namespace}' created.")
    #     except ApiException as e:
    #         print(f"Error creating namespace: {e}")
    #         self.createNamespace(namespace=namespace + "-rescue")