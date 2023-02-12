import weaviate
import time
import uuid


class DatabaseManager:
    def __init__(self, weaviate_server="http://192.168.1.110:8080"):
        self.client = weaviate.Client(weaviate_server)

    def vector_search(self, vector, class_name, retrieved_properties):
        return self.client.query.get(class_name, retrieved_properties).with_near_vector(
            {"vector": vector, "certrainty": 0.9}).with_additional("certainty").do()["data"]["Get"][class_name]

    def item_search(self, item, class_name, retrieved_properties):
        # example: self.item_search(class_name="ACI",item="Hey hey hey",retrieved_properties=["speakerData"])
        return self.client.query.get(class_name, retrieved_properties).with_near_text(
            {"concepts": item, "certainty": 0.9}).with_additional("certainty").do()["data"]["Get"][class_name]

    def class_data_uploader(self, class_name, class_data):
        retries = 0
        id = str(uuid.uuid4())
        while retries < 5:
            try:
                self.client.data_object.create(class_data, class_name, id)
                retries = 0
                return {"status": "success", "id": id}
            except:
                retries += 1
                time.sleep(0.05)
        if retries == 5:
            return {"status": "failed", "id": "failed"}

    def promptSchemaRetrieval(self, schema_name):
        response_data = \
            self.client.query.get(class_name="CorePromptSchema",
                                  properties=["schema", "requiredVars", "uuid"]).with_where(
                {"path": ["name"], "operator": "Equal", "valueText": schema_name}).do()["data"]["Get"][
                "CorePromptSchema"][0]
        return response_data

    def promptSchemaUpdate(self, schema_id, schema, requiredVars):
        response_data = self.client.data_object.update(data_object={"schema": schema, "requiredVars": requiredVars},
                                                       class_name="CorePromptSchema", uuid=schema_id)
        return response_data

    def promptSchemaUploader(self, schema, requiredVars):
        name = input("Name for this Schema: ")
        id = str(uuid.uuid4())
        self.client.data_object.create(class_name="CorePromptSchema",
                                       data_object={"name": name, "schema": schema, "requiredVars": requiredVars,
                                                    "uuid": id}, uuid=id)
