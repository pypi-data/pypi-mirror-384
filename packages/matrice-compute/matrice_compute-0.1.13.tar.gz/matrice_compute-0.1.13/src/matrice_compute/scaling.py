"""Module providing scaling functionality."""

import os
import logging
from matrice_common.utils import log_errors
# from kafka import KafkaProducer, KafkaConsumer
import uuid
import json
import time
import base64


class Scaling:

    """Class providing scaling functionality for compute instances."""

    def __init__(self, session, instance_id=None):
        """Initialize Scaling instance.

        Args:
            session: Session object for making RPC calls
            instance_id: ID of the compute instance

        Raises:
            Exception: If instance_id is not provided
        """
        if not instance_id:
            msg = "Instance id not set for this instance. Cannot perform the operation for job-scheduler without instance id"
            logging.error(msg)
            raise ValueError(msg)
        self.instance_id = instance_id
        self.session = session
        self.rpc = session.rpc
        used_ports_str = os.environ.get("USED_PORTS", "")
        self.used_ports = set(int(p) for p in used_ports_str.split(",") if p.strip())
        logging.info(
            "Initialized Scaling with instance_id: %s",
            instance_id,
        )
        # KAFKA TEMPORARILY DISABLED - Using REST API directly
        # self.kafka_config = {
        #     "bootstrap_servers": self.get_kafka_bootstrap_servers(),
        #     "api_request_topic": "action_requests",
        #     "api_response_topic": "action_responses",
        #     "scaling_request_topic": "compute_requests",
        #     "scaling_response_topic": "compute_responses"
        # }
        # self.kafka_producer = KafkaProducer(
        #     bootstrap_servers=self.kafka_config["bootstrap_servers"],
        #     value_serializer=lambda v: json.dumps(v).encode("utf-8"),)
   


    # KAFKA TEMPORARILY DISABLED - Using REST API directly
    # @log_errors(default_return=(None, "Error creating Kafka producer", "Kafka producer creation failed"), log_error=True)
    # def get_kafka_bootstrap_servers(self):
    #     """Get Kafka bootstrap servers from API and decode base64 fields."""
    #     path = "/v1/actions/get_kafka_info"
    #     response = self.rpc.get(path=path)
    #     if not response or not response.get("success"):
    #         raise ValueError(f"Failed to fetch Kafka config: {response.get('message', 'No response')}")
    #     encoded_ip = response["data"]["ip"]
    #     encoded_port = response["data"]["port"]
    #     ip = base64.b64decode(encoded_ip).decode("utf-8")
    #     port = base64.b64decode(encoded_port).decode("utf-8")
    #     bootstrap_servers = f"{ip}:{port}"
    #     return bootstrap_servers

    @log_errors(default_return=(None, "Error processing response", "Response processing failed"), log_error=True)
    def handle_response(self, resp, success_message, error_message):
        """Helper function to handle API response.

        Args:
            resp: Response from API call
            success_message: Message to log on success
            error_message: Message to log on error

        Returns:
            Tuple of (data, error, message)
        """
        if resp.get("success"):
            data = resp.get("data")
            error = None
            message = success_message
            logging.info(message)
        else:
            data = resp.get("data")
            error = resp.get("message")
            message = error_message
            logging.error("%s: %s", message, error)
        return data, error, message
         
    @log_errors(log_error=True)
    def get_downscaled_ids(self):
        """Get IDs of downscaled instances.

        Returns:
            Tuple of (data, error, message) from API response
        """
        logging.info(
            "Getting downscaled ids for instance %s",
            self.instance_id,
        )
        path = f"/v1/compute/down_scaled_ids/{self.instance_id}"
        resp = self.rpc.get(path=path)
        return self.handle_response(
            resp,
            "Downscaled ids info fetched successfully",
            "Could not fetch the Downscaled ids info",
        )

    @log_errors(default_return=(None, "API call failed", "Failed to stop instance"), log_error=True)
    def stop_instance(self):
        """Stop the compute instance.

        Returns:
            Tuple of (data, error, message) from API response
        """
        logging.info(
            "Stopping instance %s",
            self.instance_id,
        )
        path = "/v1/compute/compute_instance/stop"
        resp = self.rpc.put(
            path=path,
            payload={
                "_idInstance": self.instance_id,
                "isForcedStop": False,
            },
        )
        return self.handle_response(
            resp,
            "Instance stopped successfully",
            "Could not stop the instance",
        )
    
    @log_errors(log_error=True)
    def update_jupyter_token(
        self,
        token="",
    ):
        path = f"/v1/scaling/update_jupyter_notebook_token/{self.instance_id}"
        payload = {
            "token": token,
        }
        resp = self.rpc.put(path=path, payload=payload)
        return self.handle_response(
            resp,
            "Resources updated successfully",
            "Could not update the resources",
        )

    @log_errors(log_error=True)
    def update_action_status(
        self,
        service_provider="",
        action_record_id="",
        isRunning=True,
        status="",
        docker_start_time=None,
        action_duration=0,
        cpuUtilisation=0.0,
        gpuUtilisation=0.0,
        memoryUtilisation=0.0,
        gpuMemoryUsed=0,
        createdAt=None,
        updatedAt=None,
    ):
        """Update status of an action.

        Args:
            service_provider: Provider of the service
            action_record_id: ID of the action record
            isRunning: Whether action is running
            status: Status of the action
            docker_start_time: Start time of docker container
            action_duration: Duration of the action
            cpuUtilisation: CPU utilization percentage
            gpuUtilisation: GPU utilization percentage
            memoryUtilisation: Memory utilization percentage
            gpuMemoryUsed: GPU memory used
            createdAt: Creation timestamp
            updatedAt: Last update timestamp

        Returns:
            Tuple of (data, error, message) from API response
        """
        logging.info(
            "Updating action status for action %s",
            action_record_id,
        )
        path = "/v1/compute/update_action_status"
        payload_scaling = {
            "instanceID": self.instance_id,
            "serviceProvider": service_provider,
            "actionRecordId": action_record_id,
            "isRunning": isRunning,
            "status": status,
            "dockerContainerStartTime": docker_start_time,
            "cpuUtilisation": cpuUtilisation,
            "gpuUtilisation": gpuUtilisation,
            "memoryUtilisation": memoryUtilisation,
            "gpuMemoryUsed": gpuMemoryUsed,
            "actionDuration": action_duration,
            "createdAt": createdAt,
            "updatedAt": updatedAt,
        }
        resp = self.rpc.put(path=path, payload=payload_scaling)
        return self.handle_response(
            resp,
            "Action status details updated successfully",
            "Could not update the action status details ",
        )

    @log_errors(log_error=True)
    def update_status(
        self,
        action_record_id,
        action_type,
        service_name,
        stepCode,
        status,
        status_description,
    ):
        """Update status of an action.

        Args:
            action_record_id: ID of the action record
            action_type: Type of action
            service_name: Name of the service
            stepCode: Code indicating step in process
            status: Status to update
            status_description: Description of the status
        """
        logging.info(
            "Updating status for action %s",
            action_record_id,
        )
        url = "/v1/actions"
        payload = {
            "_id": action_record_id,
            "action": action_type,
            "serviceName": service_name,
            "stepCode": stepCode,
            "status": status,
            "statusDescription": status_description,
        }
        self.rpc.put(path=url, payload=payload)

    @log_errors(log_error=True)
    def get_shutdown_details(self):
        """Get shutdown details for the instance.

        Returns:
            Tuple of (data, error, message) from API response
        """
        logging.info(
            "Getting shutdown details for instance %s",
            self.instance_id,
        )
        path = f"/v1/compute/get_shutdown_details/{self.instance_id}"
        resp = self.rpc.get(path=path)
        return self.handle_response(
            resp,
            "Shutdown info fetched successfully",
            "Could not fetch the shutdown details",
        )

    @log_errors(log_error=True)
    def get_tasks_details(self):
        """Get task details for the instance.

        Returns:
            Tuple of (data, error, message) from API response
        """
        logging.info(
            "Getting tasks details for instance %s",
            self.instance_id,
        )
        path = f"/v1/actions/fetch_instance_action_details/{self.instance_id}/action_details"
        resp = self.rpc.get(path=path)
        return self.handle_response(
            resp,
            "Task details fetched successfully",
            "Could not fetch the task details",
        )

    @log_errors(log_error=True)
    def get_action_details(self, action_status_id):
        """Get details for a specific action using REST API.
        
        Args:
            action_status_id: ID of the action status to fetch
            
        Returns:
            Tuple of (data, error, message) from API response
        """
        logging.info("Getting action details for action %s", action_status_id)
        # KAFKA TEMPORARILY DISABLED - Using REST API directly
        # api = "get_action_details"
        # payload = {"actionRecordId": action_status_id}
        # data, error, message, kafka_response_received = self._send_kafka_request(
        #     api=api,
        #     payload=payload,
        #     request_topic=self.kafka_config["api_request_topic"],
        #     response_topic=self.kafka_config["api_response_topic"],
        #     timeout=60
        # )
        # # Check if Kafka response was received and if it's an error, log and fallback to REST API
        # if kafka_response_received:
        #     if error:
        #         logging.warning("Kafka returned error for get_action_details: %s. Falling back to REST API.", error)
        #     else:
        #         return data, error, message

        # Using REST API directly
        try:
            path = f"/v1/actions/action/{action_status_id}/details"
            resp = self.rpc.get(path=path)
            return self.handle_response(
                resp,
                "Task details fetched successfully",
                "Could not fetch the task details",
            )
        except Exception as e:
            logging.error("REST API failed (get_action_details): %s", e)
            return None, f"Failed via REST: {e}", "REST API failed"
            

    @log_errors(log_error=True)
    def update_action(
        self,
        id="",
        step_code="",
        action_type="",
        status="",
        sub_action="",
        status_description="",
        service="",
        job_params=None,
    ):
        """Update an action using REST API.
        
        Args:
            id: Action ID
            step_code: Step code
            action_type: Type of action
            status: Status of the action
            sub_action: Sub-action details
            status_description: Description of the status
            service: Service name
            job_params: Job parameters dictionary
            
        Returns:
            Tuple of (data, error, message) from API response
        """
        if job_params is None:
            job_params = {}
        logging.info("Updating action %s", id)
        # KAFKA TEMPORARILY DISABLED - Using REST API directly
        # api = "update_action"
        payload = {
            "_id": id,
            "stepCode": step_code,
            "action": action_type,
            "status": status,
            "subAction": sub_action,
            "statusDescription": status_description,
            "serviceName": service,
            "jobParams": job_params,
        }
        # data, error, message, kafka_response_received = self._send_kafka_request(
        #     api=api,
        #     payload=payload,
        #     request_topic=self.kafka_config["api_request_topic"],
        #     response_topic=self.kafka_config["api_response_topic"],
        #     timeout=60
        # )
        # # Check if Kafka response was received and if it's an error, log and fallback to REST API
        # if kafka_response_received:
        #     if error:
        #         logging.warning("Kafka returned error for update_action: %s. Falling back to REST API.", error)
        #     else:
        #         return data, error, message

        # Using REST API directly
        try:
            path = "/v1/actions"
            resp = self.rpc.put(path=path, payload=payload)
            return self.handle_response(
                resp,
                "Error logged successfully",
                "Could not log the errors",
            )
        except Exception as e:
            logging.error("REST API failed (update_action): %s", e)
            return None, f"Failed via REST: {e}", "REST API failed"
           

    @log_errors(log_error=True)
    def assign_jobs(self, is_gpu):
        """Assign jobs to the instance using REST API.
        
        Args:
            is_gpu: Boolean or any value indicating if this is a GPU instance.
                    Will be converted to proper boolean.
        
        Returns:
            Tuple of (data, error, message) from API response
        """
        # Convert is_gpu to proper boolean
        is_gpu_bool = bool(is_gpu)
        logging.info("Assigning jobs for instance %s (GPU: %s)", self.instance_id, is_gpu_bool)
        
        # KAFKA TEMPORARILY DISABLED - Using REST API directly
        # api = "assign_jobs"
        # payload = {
        #     "instanceID": self.instance_id,
        #     "isGPUInstance": is_gpu_bool,
        # }

        # data, error, message, kafka_response_received = self._send_kafka_request(
        #     api=api,
        #     payload=payload,
        #     request_topic=self.kafka_config["api_request_topic"],
        #     response_topic=self.kafka_config["api_response_topic"],
        #     timeout=60
        # )

        # # Check if Kafka response was received and if it's an error, log and fallback to REST API
        # if kafka_response_received:
        #     if error:
        #         logging.warning("Kafka returned error for assign_jobs: %s. Falling back to REST API.", error)
        #     else:
        #         return data, error, message

        # Using REST API directly
        try:
            # Convert boolean to lowercase string for API endpoint
            is_gpu_str = str(is_gpu_bool).lower()
            path = f"/v1/actions/assign_jobs/{is_gpu_str}/{self.instance_id}"
            resp = self.rpc.get(path=path)
            return self.handle_response(
                resp,
                "Pinged successfully",
                "Could not ping the scaling jobs",
            )
        except Exception as e:
            logging.error("REST API failed (assign_jobs): %s", e)
            return None, f"Failed via REST: {e}", "REST API failed"
          

    @log_errors(log_error=True)
    def update_available_resources(
        self,
        availableCPU=0,
        availableGPU=0,
        availableMemory=0,
        availableGPUMemory=0,
    ):
        """Update available resources for the instance using REST API.
        
        Args:
            availableCPU: Available CPU resources
            availableGPU: Available GPU resources
            availableMemory: Available memory
            availableGPUMemory: Available GPU memory
            
        Returns:
            Tuple of (data, error, message) from API response
        """
        logging.info("Updating available resources for instance %s", self.instance_id)
        payload = {
            "instance_id": self.instance_id,
            "availableMemory": availableMemory,
            "availableCPU": availableCPU,
            "availableGPUMemory": availableGPUMemory,
            "availableGPU": availableGPU,
        }
        # KAFKA TEMPORARILY DISABLED - Using REST API directly
        # api = "update_available_resources"
        # correlation_id = str(uuid.uuid4())

        # data, error, message, kafka_response_received = self._send_kafka_request(
        #     api=api,
        #     payload=payload,
        #     request_topic=self.kafka_config["scaling_request_topic"],
        #     response_topic=self.kafka_config["scaling_response_topic"],
        #     timeout=60
        # )

        # # Check if Kafka response was received
        # # Response format: {'correlationId': 'id', 'status': 'success'/'error', 'data': ..., 'error': 'error message'}
        # if kafka_response_received:
        #     if error:
        #         logging.warning("Kafka returned error for update_available_resources: %s. Falling back to REST API.", error)
        #     else:
        #         return data, error, message

        # Using REST API directly
        try:
            path = f"/v1/scaling/update_available_resources/{self.instance_id}"
            resp = self.rpc.put(path=path, payload=payload)
            return self.handle_response(
                resp,
                "Resources updated successfully",
                "Could not update the resources",
            )
        except Exception as e:
            logging.error("REST API failed (update_available_resources): %s", e)
            return None, f"Failed to update available resources via REST: {e}", "REST API failed"

    @log_errors(log_error=True)
    def update_action_docker_logs(self, action_record_id, log_content):
        """Update docker logs for an action using REST API.
        
        Args:
            action_record_id: ID of the action record
            log_content: Content of the logs to update
            
        Returns:
            Tuple of (data, error, message) from API response
        """
        logging.info("Updating docker logs for action %s", action_record_id)
        # KAFKA TEMPORARILY DISABLED - Using REST API directly
        # api = "update_action_docker_logs"
        payload = {
            "actionRecordId": action_record_id,
            "logContent": log_content,
        }
        # data, error, message, kafka_response_received = self._send_kafka_request(
        #     api=api,
        #     payload=payload,
        #     request_topic=self.kafka_config["api_request_topic"],
        #     response_topic=self.kafka_config["api_response_topic"],
        #     timeout=60
        # )

        # # Check if Kafka response was received and if it's an error, log and fallback to REST API
        # if kafka_response_received:
        #     if error:
        #         logging.warning("Kafka returned error for update_action_docker_logs: %s. Falling back to REST API.", error)
        #     else:
        #         return data, error, message

        # Using REST API directly
        try:
            path = "/v1/actions/update_action_docker_logs"
            resp = self.rpc.put(path=path, payload=payload)
            return self.handle_response(
                resp,
                "Docker logs updated successfully",
                "Could not update the docker logs",
            )
        except Exception as e:
            logging.error("REST API failed (update_action_docker_logs): %s", e)
            return None, f"Failed via REST: {e}", "REST API failed"
          

    @log_errors(log_error=True)
    def get_docker_hub_credentials(self):
        """Get Docker Hub credentials.

        Returns:
            Tuple of (data, error, message) from API response
        """
        logging.info("Getting docker credentials")
        path = "/v1/compute/get_docker_hub_credentials"
        resp = self.rpc.get(path=path)
        return self.handle_response(
            resp,
            "Docker credentials fetched successfully",
            "Could not fetch the docker credentials",
        )

    @log_errors(log_error=True)
    def get_open_ports_config(self):
        """Get open ports configuration.

        Returns:
            Tuple of (data, error, message) from API response
        """
        path = f"/v1/scaling/get_open_ports/{self.instance_id}"
        resp = self.rpc.get(path=path)
        return self.handle_response(
            resp,
            "Open ports config fetched successfully",
            "Could not fetch the open ports config",
        )

    @log_errors(default_return=None, log_error=True)
    def get_open_port(self):
        """Get an available open port.

        Returns:
            Port number if available, None otherwise
        """
        port_range = {"from": 8200, "to": 9000}
        try:
            resp, err, msg = self.get_open_ports_config()
            if not err and resp and resp[0]:
                port_range = resp[0]
            else:
                logging.warning("Using default port range 8200-9000 due to config fetch error")
        except Exception as err:
            logging.warning(
                "Using default port range 8200-9000. Config fetch failed: %s",
                str(err),
            )
        min_port = port_range["from"]
        max_port = port_range["to"]
        for port in range(min_port, max_port):
            if port in self.used_ports:
                continue
            self.used_ports.add(port)
            ports_value = ",".join(str(p) for p in self.used_ports)
            os.environ["USED_PORTS"] = str(ports_value)
            logging.info("Found available port: %s", port)
            return port
        logging.error(
            "No available ports found in range %s-%s",
            min_port,
            max_port,
        )
        return None

    @log_errors(default_return="", log_error=False)
    def get_data_processing_image(self):
        """Get data processing image name.

        Returns:
            Full image name including repository and tag
        """
        logging.info("Getting data processing image")
        return f"285699223019.dkr.ecr.us-west-2.amazonaws.com/{os.environ.get('ENV', 'prod')}-data-processing:latest"

    @log_errors(log_error=True)
    def get_model_secret_keys(self, secret_name):
        """Get model secret keys.

        Args:
            secret_name: Name of the secret

        Returns:
            Tuple of (data, error, message) from API response
        """
        path = f"/v1/scaling/get_models_secret_keys?secret_name={secret_name}"
        resp = self.rpc.get(path=path)
        return self.handle_response(
            resp,
            "Secret keys fetched successfully",
            "Could not fetch the secret keys",
        )

    @log_errors(log_error=True)
    def get_model_codebase(self, model_family_id):
        """Get model codebase.

        Args:
            model_family_id: ID of the model family

        Returns:
            Tuple of (data, error, message) from API response
        """
        path = f"/v1/model_store/get_user_code_download_path/{model_family_id}"
        resp = self.rpc.get(path=path)
        return self.handle_response(
            resp,
            "Codebase fetched successfully",
            "Could not fetch the codebase",
        )

    @log_errors(log_error=True)
    def get_model_codebase_requirements(self, model_family_id):
        """Get model codebase requirements.

        Args:
            model_family_id: ID of the model family

        Returns:
            Tuple of (data, error, message) from API response
        """
        path = f"/v1/model_store/get_user_requirements_download_path/{model_family_id}"
        resp = self.rpc.get(path=path)
        return self.handle_response(
            resp,
            "Codebase requirements fetched successfully",
            "Could not fetch the codebase requirements",
        )

    @log_errors(log_error=True)
    def get_model_codebase_script(self, model_family_id):
        """Get model codebase script.

        Args:
            model_family_id: ID of the model family

        Returns:
            Tuple of (data, error, message) from API response
        """
        path = f"/v1/model_store/get_user_script_download_path/:{model_family_id}"
        resp = self.rpc.get(path=path)
        return self.handle_response(
            resp,
            "Codebase script fetched successfully",
            "Could not fetch the codebase script",
        )

    @log_errors(log_error=True)
    def add_account_compute_instance(
        self,
        account_number,
        alias,
        service_provider,
        instance_type,
        shut_down_time,
        lease_type,
        launch_duration,
    ):
        """Add a compute instance for an account.

        Args:
            account_number: Account number
            alias: Instance alias
            service_provider: Cloud service provider
            instance_type: Type of instance
            shut_down_time: Time to shutdown
            lease_type: Type of lease
            launch_duration: Duration to launch

        Returns:
            Tuple of (data, error, message) from API response
        """
        path = "/v1/scaling/add_account_compute_instance"
        payload = {
            "accountNumber": account_number,
            "alias": alias,
            "serviceProvider": service_provider,
            "instanceType": instance_type,
            "shutDownTime": shut_down_time,
            "leaseType": lease_type,
            "launchDuration": launch_duration,
        }
        resp = self.rpc.post(path=path, payload=payload)
        return self.handle_response(
            resp,
            "Compute instance added successfully",
            "Could not add the compute instance",
        )

    @log_errors(log_error=True)
    def stop_account_compute(self, account_number, alias):
        """Stop a compute instance for an account.

        Args:
            account_number: Account number
            alias: Instance alias

        Returns:
            Tuple of (data, error, message) from API response
        """
        path = f"/v1/scaling/stop_account_compute/{account_number}/{alias}"
        resp = self.rpc.put(path=path)
        return self.handle_response(
            resp,
            "Compute instance stopped successfully",
            "Could not stop the compute instance",
        )

    @log_errors(log_error=True)
    def restart_account_compute(self, account_number, alias):
        """Restart a compute instance for an account.

        Args:
            account_number: Account number
            alias: Instance alias

        Returns:
            Tuple of (data, error, message) from API response
        """
        path = f"/v1/scaling/restart_account_compute/{account_number}/{alias}"
        resp = self.rpc.put(path=path)
        return self.handle_response(
            resp,
            "Compute instance restarted successfully",
            "Could not restart the compute instance",
        )

    @log_errors(log_error=True)
    def delete_account_compute(self, account_number, alias):
        """Delete a compute instance for an account.

        Args:
            account_number: Account number
            alias: Instance alias

        Returns:
            Tuple of (data, error, message) from API response
        """
        path = f"/v1/scaling/delete_account_compute/{account_number}/{alias}"
        resp = self.rpc.delete(path=path)
        return self.handle_response(
            resp,
            "Compute instance deleted successfully",
            "Could not delete the compute instance",
        )

    @log_errors(log_error=True)
    def get_all_instances_type(self):
        """Get all instance types.

        Returns:
            Tuple of (data, error, message) from API response
        """
        path = "/v1/scaling/get_all_instances_type"
        resp = self.rpc.get(path=path)
        return self.handle_response(
            resp,
            "All instance types fetched successfully",
            "Could not fetch the instance types",
        )

    @log_errors(log_error=True)
    def get_compute_details(self):
        """Get compute instance details.

        Returns:
            Tuple of (data, error, message) from API response
        """
        path = f"/v1/scaling/get_compute_details/{self.instance_id}"
        resp = self.rpc.get(path=path)
        return self.handle_response(
            resp,
            "Compute details fetched successfully",
            "Could not fetch the compute details",
        )

    @log_errors(log_error=True)
    def get_user_access_key_pair(self, user_id):
        """Get user access key pair.

        Args:
            user_id: ID of the user

        Returns:
            Tuple of (data, error, message) from API response
        """
        path = f"/v1/compute/get_user_access_key_pair/{user_id}/{self.instance_id}"
        resp = self.rpc.get(path=path)
        return self.handle_response(
            resp,
            "User access key pair fetched successfully",
            "Could not fetch the user access key pair",
        )

    @log_errors(log_error=True)
    def get_internal_api_key(self, action_id):
        """Get internal API key.

        Args:
            action_id: ID of the action

        Returns:
            Tuple of (data, error, message) from API response
        """
        path = f"/v1/actions/get_internal_api_key/{action_id}/{self.instance_id}"
        resp = self.rpc.get(path=path)
        return self.handle_response(
            resp,
            "internal keys fetched successfully",
            "Could not fetch internal keys",
        )

    # KAFKA TEMPORARILY DISABLED - Using REST API directly
    # @log_errors(log_error=True)
    # def handle_kafka_response(self, msg, success_message, error_message):
    #     """
    #     Helper to process Kafka response messages in a consistent way.
    #     """
    #     if msg.get("status") == "success":
    #         data = msg.get("data")
    #         error = None
    #         message = success_message
    #         logging.info(message)
    #     else:
    #         data = msg.get("data")
    #         error = msg.get("error", "Unknown error")
    #         message = error_message
    #         logging.error("%s: %s", message, error)
    #     return data, error, message

    # def _send_kafka_request(self, api, payload, request_topic, response_topic, timeout=60):
    #     """
    #     Helper to send a request to Kafka and wait for a response.
    #     Returns (data, error, message, kafka_response_received) where kafka_response_received is True if a response was received (even if error), False if transport error/timeout.
    #     """
    #     correlation_id = str(uuid.uuid4())
    #     request_message = {
    #         "correlationId": correlation_id,
    #         "api": api,
    #         "payload": payload,
    #     }

    #     consumer = KafkaConsumer(
    #         response_topic,
    #         bootstrap_servers=self.kafka_config["bootstrap_servers"],
    #         group_id=None,
    #         value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    #         auto_offset_reset='latest',
    #         enable_auto_commit=True,
    #     )

    #     try:
    #         if hasattr(self.session.rpc, 'AUTH_TOKEN'):
    #             self.session.rpc.AUTH_TOKEN.set_bearer_token()
    #             auth_token = self.session.rpc.AUTH_TOKEN.bearer_token
    #             auth_token = auth_token.replace("Bearer ", "")
    #             headers = [("Authorization", bytes(f"{auth_token}", "utf-8"))]
    #         else:
    #             headers = None
    #         self.kafka_producer.send(request_topic, request_message, headers=headers)
    #         # self.kafka_producer.flush()
    #         logging.info("Sent %s request to Kafka topic %s", api, request_topic)
    #     except Exception as e:
    #         logging.error("Kafka producer error: %s", e)
    #         return None, f"Kafka producer error: {e}", "Kafka send failed", False
    #     try:
    #         start = time.time()
    #         while time.time() - start < timeout:
    #             # Poll for messages with a short timeout to avoid blocking forever
    #             message_batch = consumer.poll(timeout_ms=1000)
    #             if message_batch:
    #                 for topic_partition, messages in message_batch.items():
    #                     for message in messages:
    #                         print("trying to fetch message")
    #                         msg = message.value
    #                         if msg.get("correlationId") == correlation_id:
    #                             consumer.close()
    #                             # Always treat a received response as final, even if error
    #                             return self.handle_kafka_response(
    #                                 msg,
    #                                 f"Fetched via Kafka for {api}",
    #                                 f"Kafka error response for {api}"
    #                             ) + (True,)
    #             else:
    #                 print(f"No messages received, waiting... ({time.time() - start:.1f}s/{timeout}s)")
    #
    #         consumer.close()
    #         logging.warning("Kafka response timeout for %s after %d seconds", api, timeout)
    #         return None, "Kafka response timeout", "Kafka response timeout", False
    #     except Exception as e:
    #         logging.error("Kafka consumer error: %s", e)
    #         return None, f"Kafka consumer error: {e}", "Kafka consumer error", False

    # def _cache_failed_request(self, api, payload):
    #     """Cache the failed request for retry. Here, we use a simple file cache as a placeholder."""
    #     try:
    #         cache_file = os.path.join(os.path.dirname(__file__), 'request_cache.json')
    #         if os.path.exists(cache_file):
    #             with open(cache_file, 'r') as f:
    #                 cache = json.load(f)
    #         else:
    #             cache = []
    #         cache.append({"api": api, "payload": payload, "ts": time.time()})
    #         with open(cache_file, 'w') as f:
    #             json.dump(cache, f)
    #         logging.info("Cached failed request for api %s", api)
    #     except Exception as e:
    #         logging.error("Failed to cache request: %s", e)