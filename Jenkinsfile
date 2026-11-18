// Step 3: run Jenkins in Docker and point a pipeline job at this repo.
pipeline {
  agent any
  environment {
    IMAGE = "txn-consumer:${env.BUILD_NUMBER}"
  }
  stages {
    stage('Install') {
      steps {
        sh 'python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt'
      }
    }
    stage('Unit tests') {
      steps {
        sh '. .venv/bin/activate && pytest -q'
      }
    }
    stage('dbt build (CI schema)') {
      when { expression { return env.SNOWFLAKE_ACCOUNT != null } }
      steps {
        sh '. .venv/bin/activate && pip install dbt-snowflake && cd dbt && dbt build --target dev'
      }
    }
    stage('Docker image') {
      steps {
        sh 'docker build -t $IMAGE .'
      }
    }
    stage('Deploy to Kubernetes') {
      when { branch 'main' }
      steps {
        sh 'kubectl apply -f k8s/'
      }
    }
  }
}
