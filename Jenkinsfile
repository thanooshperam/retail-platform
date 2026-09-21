```groovy
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

        stage('Record Previous Version') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                script {

                    def previousImage = ""

                    bat """
                        docker inspect ${CONTAINER_NAME} --format="{{.Config.Image}}" > previous-image.txt 2>nul
                    """

                    if (fileExists('previous-image.txt')) {
                        previousImage = readFile('previous-image.txt').trim()
                    }

                    if (previousImage == "") {
                        env.PREVIOUS_IMAGE = "${IMAGE_NAME}:4.2.1"
                    } else {
                        env.PREVIOUS_IMAGE = previousImage
                    }

                    echo "Previous production image: ${env.PREVIOUS_IMAGE}"
                }
            }
        }

        stage('Deploy New Version') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                script {

                    echo "Starting new version ${params.VERSION}..."

                    bat """
                        docker run -d ^
                        --name retail-app-new ^
                        -p 8082:8081 ^
                        --network ${NETWORK_NAME} ^
                        -e APP_VERSION=${params.VERSION} ^
                        -e HEALTH_MODE=healthy ^
                        ${IMAGE_NAME}:${params.VERSION}
                    """

                    echo "New version started on temporary port 8082."
                }
            }
        }

        stage('Health Check New Version') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                script {

                    echo "Waiting for new version health check..."

                    bat """
                        powershell -Command "Start-Sleep -Seconds 15"
                    """

                    def healthResult = bat(
                        script: """
                            powershell -Command "try { \$r = Invoke-WebRequest -Uri http://localhost:8082/health -UseBasicParsing; Write-Host \$r.Content; if (\$r.StatusCode -ne 200) { exit 1 } } catch { Write-Host 'HEALTH CHECK FAILED'; exit 1 }"
                        """,
                        returnStatus: true
                    )

                    if (healthResult != 0) {

                        echo "NEW VERSION HEALTH CHECK FAILED."

                        echo "Stopping failed new version..."

                        bat """
                            docker rm -f retail-app-new 2>nul || exit /b 0
                        """

                        echo "Restoring previous image: ${env.PREVIOUS_IMAGE}"

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
                            ${env.PREVIOUS_IMAGE}
                        """

                        echo "Previous version restored."

                        error("Deployment failed. Automatic rollback completed.")
                    }

                    echo "New version health check PASSED."
                }
            }
        }

        stage('Switch To New Version') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                script {

                    echo "Health check passed."
                    echo "Switching production container to version ${params.VERSION}."

                    bat """
                        docker rm -f ${CONTAINER_NAME} 2>nul || exit /b 0
                    """

                    bat """
                        docker rename retail-app-new ${CONTAINER_NAME}
                    """

                    echo "Production switched to ${params.VERSION}."
                }
            }
        }

        stage('Final Health Check') {
            when {
                expression {
                    params.DEPLOYMENT_ACTION == 'DEPLOY'
                }
            }

            steps {
                script {

                    bat """
                        powershell -Command "Start-Sleep -Seconds 5"
                    """

                    def finalHealth = bat(
                        script: """
                            powershell -Command "try { \$r = Invoke-WebRequest -Uri http://localhost:${PORT}/health -UseBasicParsing; Write-Host \$r.Content; if (\$r.StatusCode -ne 200) { exit 1 } } catch { Write-Host 'FINAL HEALTH CHECK FAILED'; exit 1 }"
                        """,
                        returnStatus: true
                    )

                    if (finalHealth != 0) {
                        error("Final production health check failed.")
                    }

                    echo "Final production health check PASSED."
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

                    echo "Manual rollback to version 4.2.1..."

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

                    echo "Rollback to 4.2.1 completed."
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
```
