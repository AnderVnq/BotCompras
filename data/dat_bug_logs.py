from data.dat_conection import DBConfigMySQL
import json

class BugLogogger:


    def __init__(self):
        self.conection=DBConfigMySQL()



    def createLog(self,message,severity="ERROR",module="SheinBuyBot",stack_trace=None):
        sp_name="SP_BugLogsCreate"

        data=[{"log_description":message,"severity":severity,"module":module,"stack_trace":stack_trace}]
        try:
            conection=self.conection.connect()
            conection.autocommit=True
            json_data=json.dumps(data)
            with conection.cursor() as cursor:
                cursor.execute(f"CALL {sp_name}(%s);",(json_data,))
        except Exception as e:
            print(e)
        finally:
            self.conection.disconnect()


