import pymysql


class DbClass:
    def __init__(self):
        self.db = pymysql.connect(host="127.0.0.1", db="test",
                                  cursorclass=pymysql.cursors.DictCursor)
        self.cursor = self.db.cursor()

    def read(self, query, parameters):
        self.cursor.execute(query, parameters)
        menus = self.cursor.fetchall()
        return menus

    def update(self, query, parameters):
        self.cursor.execute(query, parameters)
        self.db.commit()

    def simple_update(self, query):
        self.cursor.execute(query)
        self.db.commit()

    def close(self):
        self.cursor.close()
        self.db.close()


query1 = "select appointment_no from appointment where Specialist = %s"
query2 = "update appointment set appointment_no = %s, time = curdate() where Specialist = %s"
query3 = "update appointment set appointment_no = 0 where time < curdate()"
