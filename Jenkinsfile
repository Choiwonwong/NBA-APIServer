pipeline {
    agent any
    
    // 환경변수 지정
    environment {
        REGION='ap-northeast-1'
        ECR_PATH='dkr.ecr.ap-northeast-1.amazonaws.com'
        ACCOUNT_ID='622164100401'
        AWS_CREDENTIAL_NAME='NBA-AWS-Credential-v2'
        IMAGE_NAME = 'quest-api'
        IMAGE_VERSION = "0.0.1"
    }
    stages {

        stage('Checkout') {
            steps {
                git branch: 'main',
                    credentialsId: 'NBA-Web-API-Gitops-Pipeline-Credential',
                    url: 'https://github.com/Choiwonwong/NBA-APIServer.git'
            }
        }
        // stage('CORS Origin Registry') {
        //     steps {                
        //         sh '''
        //         kubectl get secrets cors-origin -n quest &&  kubectl delete secret cors-origin -n quest
        //         kubectl create secret generic cors-origin --from-literal=WEB_URL=$(kubectl get svc quest-web-service -n quest -o jsonpath="{.status.loadBalancer.ingress[0].hostname}") -n quest
        //         '''
        //     } 
        // }
        stage('build') {
            steps {
                sh '''
        		 docker build -t $ACCOUNT_ID.$ECR_PATH/$IMAGE_NAME:$IMAGE_VERSION .
        		 '''
            }
        }
        stage('upload aws ECR') {
            steps {                
                script {
                    docker.withRegistry("https://$ACCOUNT_ID.$ECR_PATH", "ecr:$REGION:$AWS_CREDENTIAL_NAME") {
                        docker.image("$ACCOUNT_ID.$ECR_PATH/$IMAGE_NAME:$IMAGE_VERSION").push()
                    }
                }
            } 
        }
        stage('Deploy in NBA EKS') {
            steps {                
                sh 'kubectl apply -f manifest/deployment.yaml'
            } 
        }
    }
}


