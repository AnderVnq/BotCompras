from data.dat_bug_logs import BugLogogger
from data.dat_conection import DBConfigMySQL
import json


class SheinBotProcessor:

    def __init__(self):
        self.con=DBConfigMySQL()
        self.bug_logger = BugLogogger()


    
    def get_data_shein_by_skus(self,list_skus):
        sp_name = f"SP_get_data_by_sku_for_bot_shein"
        try:
            lis_json=json.dumps(list_skus)
            connection = self.con.connect()
            with connection.cursor() as cursor:
                cursor.execute("SET @result = '';")
                cursor.execute(f"CALL {sp_name}(%s,@result);",(lis_json,))
                cursor.execute("SELECT @result;")
                result = cursor.fetchone()[0]
                json_data = json.loads(result) if result else []
                return json_data
        except Exception as e:
            self.bug_logger.createLog(f"Error in get_data_shein_by_skus",stack_trace=str(e))
            return []
        finally:
            self.con.disconnect()