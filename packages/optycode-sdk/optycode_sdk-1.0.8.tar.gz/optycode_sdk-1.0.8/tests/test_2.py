from optycode_sdk import OptycodeAPI

client = OptycodeAPI(auth_token="")
client.log_data_async(user_question="sdk test", model_answer="sdk answer", model_id=2, session_id=2, model_input="sdk model input", question_id="bobip")
# response = client.send_model_data(question="sdk_test_normal_gateway", answer="sdk_test_answer_normal_gatewat", model_id=2)
