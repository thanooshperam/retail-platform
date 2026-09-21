pipeline {

    agent any

    parameters {

        choice(
            name: 'DEPLOYMENT_ACTION',
            choices: ['DEPLOY', 'ROLLBACK'],
            description: 'Select deployment action'
        )

        choice(
            name: 'ENVIRONMENT',
            choices: ['UAT', 'PRODUCTION'],
            description: 'Select environment'
        )

        string(
            name: 'VERSION',
            defaultValue: '4.2.1',
            description: 'Application version'
        )

        choice(
            name: 'CONFIRM_PROD',
            choices: ['NO', 'YES'],
            description: 'Production confirmation'
        )
    }

    environment {
        IMAGE_NAME = 'retail-app'
        CONTAINER_NAME = 'retail-app'
        NETWORK_NAME = 'retail-network'
        PORT = '8081'
    }

    stages {

        stage('Validate Parameters') {
            steps {
                script {
                    echo "Deployment Action: ${params.DEPLOYMENT_ACTION}"
                    echo "Environment: ${params.ENVIRONMENT}"
                    echo "Version: ${params.VERSION}"
                    echo "Production Confirmation: ${params.CONFIRM_PROD}"

                    if (params.ENVIRONMENT == 'PRODUCTION' &&
                        params.CONFIRM_PROD != 'YES') {

                        error("Production deployment blocked. CONFIRM_PROD must be YES.")
                    }
                }
            }
        }

        stage('Checkout Code') {
            steps {
                checkout scm

                bat 'git rev-parse HEAD'
            }
        }

        stage('Validate Git Tag') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                bat "git show-ref --tags --verify --quiet refs/tags/v${params.VERSION}"

                echo "Git tag v${params.VERSION} exists."
            }
        }

        stage('Build Docker Image') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                bat "docker build -t ${IMAGE_NAME}:${params.VERSION} ."
            }
        }

        stage('Deploy') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                script {

                    echo "Stopping previous container if it exists..."

                    bat """
                        docker rm -f ${CONTAINER_NAME} 2>nul || exit /b 0
                    """

                    echo "Starting version ${params.VERSION}..."

                    bat """
                        docker run -d ^
                        --name ${CONTAINER_NAME} ^
                        -p ${PORT}:${PORT} ^
                        --network ${NETWORK_NAME} ^
                        -e APP_VERSION=${params.VERSION} ^
                        -e HEALTH_MODE=healthy ^
                        ${IMAGE_NAME}:${params.VERSION}
                    """
                }
            }
        }

        stage('Health Check') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                script {

                    echo "Waiting for application..."

                    bat """
                        powershell -Command "Start-Sleep -Seconds 15"
                    """

                    def healthResult = bat(
                        script: """
                            powershell -Command "try { \$r = Invoke-WebRequest -Uri http://localhost:${PORT}/health -UseBasicParsing; Write-Host \$r.Content; if (\$r.StatusCode -ne 200) { exit 1 } } catch { Write-Host 'HEALTH CHECK FAILED'; exit 1 }"
                        """,
                        returnStatus: true
                    )

                    if (healthResult != 0) {

                        echo "Health check FAILED."

                        echo "Stopping failed deployment..."

                        bat """
                            docker rm -f ${CONTAINER_NAME} 2>nul || exit /b 0
                        """

                        echo "Restoring version 4.2.1..."

                        bat """
                            docker run -d ^
                            --name ${CONTAINER_NAME} ^
                            -p ${PORT}:${PORT} ^
                            --network ${NETWORK_NAME} ^
                            -e APP_VERSION=4.2.1 ^
                            -e HEALTH_MODE=healthy ^
                            ${IMAGE_NAME}:4.2.1
                        """

                        error("Deployment failed. Automatic rollback completed.")
                    }

                    echo "Health check PASSED."
                }
            }
        }

        stage('Rollback') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'ROLLBACK'
                }
            }

            steps {
                script {

                    echo "Rolling back to version 4.2.1..."

                    bat """
                        docker rm -f ${CONTAINER_NAME} 2>nul || exit /b 0
                    """

                    bat """
                        docker run -d ^
                        --name ${CONTAINER_NAME} ^
                        -p ${PORT}:${PORT} ^
                        --network ${NETWORK_NAME} ^
                        -e APP_VERSION=4.2.1 ^
                        -e HEALTH_MODE=healthy ^
                        ${IMAGE_NAME}:4.2.1
                    """

                    echo "Rollback completed."
                }
            }
        }
    }

    post {

        success {
            echo "=============================="
            echo "DEPLOYMENT SUCCESSFUL"
            echo "=============================="

            bat "docker ps"
        }

        failure {
            echo "=============================="
            echo "DEPLOYMENT FAILED / ROLLBACK"
            echo "=============================="

            bat "docker ps -a"
        }

        always {
            echo "Final Docker state:"
            bat "docker ps -a"
        }
    }
}