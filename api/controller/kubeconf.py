# This Controller doesn't use in this project.
# Just for reference.
# Failed to use this controller because of the error below.

# import json
# import boto3

# class kubeconfigController:
#     def __init__(self, region, cluster_name, access_key, secret_key):
#         self.region = region
#         self.cluster_name = cluster_name
#         self.access_key = access_key
#         self.secret_key = secret_key

#     def createConfig(self):
#         eks_client = boto3.client('eks', region_name=self.region,
#                     aws_access_key_id=self.access_key,
#                     aws_secret_access_key=self.secret_key)
#         iam_client = boto3.client('iam', region_name=self.region, 
#                     aws_access_key_id=self.access_key,
#                     aws_secret_access_key=self.secret_key)
        
#         cluster_ca = eks_client.describe_cluster(name=self.cluster_name)['cluster']['certificateAuthority']['data']
#         cluster_endpoint = eks_client.describe_cluster(name=self.cluster_name)['cluster']['endpoint']

#         caller_identity = boto3.client('sts', region_name=self.region, 
#                     aws_access_key_id=self.access_key,
#                     aws_secret_access_key=self.secret_key).get_caller_identity()
#         account_id = caller_identity['Account']

#         # IAM 사용자 생성
#         user_name = f"{self.cluster_name}-user"
#         iam_client.create_user(UserName=user_name)

#         response = iam_client.create_access_key(UserName=user_name)
#         access_key = response['AccessKey']['AccessKeyId']
#         secret_key = response['AccessKey']['SecretAccessKey']

#         # 클러스터 권한 정책 생성 및 연결
#         policy_document = {
#             "Version": "2012-10-17",
#             "Statement": [
#                 {
#                     "Effect": "Allow",
#                     "Action": "eks:DescribeCluster",
#                     "Resource": f"arn:aws:eks:{self.region}:{account_id}:cluster/{self.cluster_name}"
#                 },
#                 {
#                     "Effect": "Allow",
#                     "Action": "eks:ListClusters",
#                     "Resource": "*"
#                 }
#             ]
#         }
#         policy_name = f"{self.cluster_name}-policy"
#         policy_arn = iam_client.create_policy(
#             PolicyName=policy_name,
#             PolicyDocument=json.dumps(policy_document)
#         )['Policy']['Arn']
#         iam_client.attach_user_policy(UserName=user_name, PolicyArn=policy_arn)

#         kubeconfig = f'''apiVersion: v1
# clusters:
# - cluster:
#     server: {cluster_endpoint}
#     certificate-authority-data: {cluster_ca}
#   name: arn:aws:eks:{self.region}:{account_id}:cluster/{self.cluster_name}
# contexts:
# - context:
#     cluster: arn:aws:eks:{self.region}:{account_id}:cluster/{self.cluster_name}
#     user: arn:aws:eks:{self.region}:{account_id}:cluster/{self.cluster_name}
#   name: arn:aws:eks:{self.region}:{account_id}:cluster/{self.cluster_name}
# current-context: arn:aws:eks:{self.region}:{account_id}:cluster/{self.cluster_name}
# kind: Config
# preferences: {{}}
# users:
# - name: arn:aws:eks:{self.region}:{account_id}:cluster/{self.cluster_name}
#   user:
#     exec:
#       apiVersion: client.authentication.k8s.io/v1beta1
#       command: aws
#       args:
#         - --region
#         - {self.region}
#         - eks
#         - get-token
#         - --cluster-name
#         - {self.cluster_name}
#       env:
#         - name: "AWS_PROFILE"
#           value: "{user_name}"
#         - name: "AWS_ACCESS_KEY_ID"
#           value: "{access_key}"
#         - name: "AWS_SECRET_ACCESS_KEY"
#           value: "{secret_key}"'''
#         return kubeconfig