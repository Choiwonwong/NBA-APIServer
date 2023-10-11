pipeline {
    agent any
    
    // 환경변수 지정
    environment {
        REGION='ap-northeast-1' // 이거 Public Region이라서 그럼
        ECR_PATH='dkr.ecr.ap-northeast-1.amazonaws.com'
        ACCOUNT_ID='622164100401'
        AWS_CREDENTIAL_NAME='NBA-AWS-Credential'
        IMAGE_NAME = 'nba-api'
        IMAGE_VERSION = "test-1.1.0"
    }
    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    credentialsId: 'NBA-Web-API-Gitops-Pipeline-Credential',
                    url: 'https://github.com/Choiwonwong/NBA-APIServer.git'
            }
        }
        
        stage('build') {
            steps {
                sh '''
        		 docker build -t $ACCOUNT_ID.$ECR_PATH/$IMAGE_NAME:$IMAGE_VERSION .
        		 '''
            }
        }
    
        stage('upload aws ECR') {
            steps {                
                sh 'rm  ~/.dockercfg || true'
                sh 'rm ~/.docker/config.json || true'
                script {
                    docker.withRegistry("https://$ACCOUNT_ID.$ECR_PATH", "ecr:$REGION:NBA-AWS-Credential") {
                        docker.image("$ACCOUNT_ID.$ECR_PATH/$IMAGE_NAME:$IMAGE_VERSION").push()
                    }
                }
            } 
        }

        stage('Deploy in NBA EKS') {
            steps {                
                sh 'kubectl apply -f manifest/deploy.yaml'
            } 
        }
    }
}


