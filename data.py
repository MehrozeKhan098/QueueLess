import os
import pandas as pd
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    connection = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA")
    )

    return connection


# ========================================================
# SERVICES
# ========================================================

def get_services():

    connection = get_connection()

    query = """
        SELECT
            SERVICE_ID,
            SERVICE_CODE,
            SERVICE_NAME,
            AVG_SERVICE_TIME,
            DESCRIPTION
        FROM SERVICES
        ORDER BY SERVICE_ID
    """

    data = pd.read_sql(query, connection)

    connection.close()

    return data


# ========================================================
# PATIENTS
# ========================================================

def get_patients():

    connection = get_connection()

    query = """
        SELECT
            PATIENT_ID,
            PATIENT_NAME,
            AGE,
            GENDER,
            PHONE,
            CREATED_AT
        FROM PATIENTS
        ORDER BY PATIENT_ID
    """

    data = pd.read_sql(query, connection)

    connection.close()

    return data


# ========================================================
# QUEUE
# ========================================================

def get_queue():

    connection = get_connection()

    query = """
        SELECT
            q.QUEUE_ID,
            q.TOKEN_NUMBER,
            q.PATIENT_ID,
            p.PATIENT_NAME,
            q.SERVICE_ID,
            s.SERVICE_NAME,
            q.QUEUE_POSITION,
            q.STATUS,
            q.ARRIVAL_TIME,
            q.ESTIMATED_WAIT_TIME,
            q.DOCTOR_NAME
        FROM QUEUE q
        JOIN PATIENTS p
            ON q.PATIENT_ID = p.PATIENT_ID
        JOIN SERVICES s
            ON q.SERVICE_ID = s.SERVICE_ID
        ORDER BY
            q.SERVICE_ID,
            q.QUEUE_POSITION
    """

    data = pd.read_sql(query, connection)

    connection.close()

    return data


# ========================================================
# PATIENT QUEUE
# ========================================================

def get_patient_queue(token_number):

    connection = get_connection()

    query = """
        SELECT
            q.QUEUE_ID,
            q.TOKEN_NUMBER,
            q.PATIENT_ID,
            p.PATIENT_NAME,
            q.SERVICE_ID,
            s.SERVICE_NAME,
            q.QUEUE_POSITION,
            q.STATUS,
            q.ARRIVAL_TIME,
            q.ESTIMATED_WAIT_TIME,
            q.DOCTOR_NAME
        FROM QUEUE q
        JOIN PATIENTS p
            ON q.PATIENT_ID = p.PATIENT_ID
        JOIN SERVICES s
            ON q.SERVICE_ID = s.SERVICE_ID
        WHERE q.TOKEN_NUMBER = %s
    """

    data = pd.read_sql(
        query,
        connection,
        params=(token_number,)
    )

    connection.close()

    return data


# ========================================================
# SERVICE QUEUE
# ========================================================

def get_service_queue(service_id):

    connection = get_connection()

    query = """
        SELECT
            q.QUEUE_ID,
            q.TOKEN_NUMBER,
            p.PATIENT_NAME,
            s.SERVICE_NAME,
            q.QUEUE_POSITION,
            q.STATUS,
            q.ESTIMATED_WAIT_TIME,
            q.DOCTOR_NAME
        FROM QUEUE q
        JOIN PATIENTS p
            ON q.PATIENT_ID = p.PATIENT_ID
        JOIN SERVICES s
            ON q.SERVICE_ID = s.SERVICE_ID
        WHERE q.SERVICE_ID = %s
        ORDER BY q.QUEUE_POSITION
    """

    data = pd.read_sql(
        query,
        connection,
        params=(service_id,)
    )

    connection.close()

    return data


# ========================================================
# STAFF
# ========================================================

def get_staff():

    connection = get_connection()

    query = """
        SELECT
            STAFF_ID,
            STAFF_NAME,
            ROLE,
            DEPARTMENT,
            SERVICE_ID,
            STATUS
        FROM STAFF
        ORDER BY STAFF_ID
    """

    data = pd.read_sql(query, connection)

    connection.close()

    return data


# ========================================================
# ADD PATIENT
# ========================================================

def add_patient_to_snowflake(
    patient_name,
    age,
    gender,
    phone
):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        query = """
            INSERT INTO PATIENTS
            (
                PATIENT_NAME,
                AGE,
                GENDER,
                PHONE
            )
            VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                patient_name,
                age,
                gender,
                phone
            )
        )

        connection.commit()

    finally:

        cursor.close()
        connection.close()


# ========================================================
# GET LATEST PATIENT ID
# ========================================================

def get_latest_patient_id():

    connection = get_connection()

    try:

        cursor = connection.cursor()

        query = """
            SELECT PATIENT_ID
            FROM PATIENTS
            ORDER BY PATIENT_ID DESC
            LIMIT 1
        """

        cursor.execute(query)

        result = cursor.fetchone()

        if result:
            return result[0]

        return None

    finally:

        cursor.close()
        connection.close()


# ========================================================
# GET SERVICE ID
# ========================================================

def get_service_id(service_name):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        query = """
            SELECT SERVICE_ID
            FROM SERVICES
            WHERE SERVICE_NAME = %s
        """

        cursor.execute(
            query,
            (service_name,)
        )

        result = cursor.fetchone()

        if result:
            return result[0]

        return None

    finally:

        cursor.close()
        connection.close()


# ========================================================
# ADD QUEUE ENTRY
# ========================================================

def add_queue_entry(
    patient_id,
    service_id,
    token_number,
    queue_position,
    status,
    estimated_wait_time,
    doctor_name
):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        query = """
            INSERT INTO QUEUE
            (
                PATIENT_ID,
                SERVICE_ID,
                TOKEN_NUMBER,
                QUEUE_POSITION,
                STATUS,
                ESTIMATED_WAIT_TIME,
                DOCTOR_NAME
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (
                patient_id,
                service_id,
                token_number,
                queue_position,
                status,
                estimated_wait_time,
                doctor_name
            )
        )

        connection.commit()

    finally:

        cursor.close()
        connection.close()


# ========================================================
# CANCEL TOKEN
# ========================================================

def cancel_queue_token(token_number):

    connection = get_connection()

    try:

        cursor = connection.cursor()

        query = """
            UPDATE QUEUE
            SET STATUS = 'Cancelled'
            WHERE TOKEN_NUMBER = %s
              AND UPPER(STATUS) = 'WAITING'
        """

        cursor.execute(
            query,
            (token_number,)
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:

        cursor.close()
        connection.close()


# ========================================================
# SERVE NEXT PATIENT
# ========================================================

def serve_next_patient():

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # Current serving patient becomes served
        cursor.execute("""
            UPDATE QUEUE
            SET STATUS = 'Served'
            WHERE UPPER(STATUS) = 'SERVING'
        """)

        # Find next waiting patient
        cursor.execute("""
            SELECT QUEUE_ID
            FROM QUEUE
            WHERE UPPER(STATUS) = 'WAITING'
            ORDER BY QUEUE_POSITION
            LIMIT 1
        """)

        result = cursor.fetchone()

        if result is None:

            connection.commit()

            return None

        next_queue_id = result[0]

        # Next patient becomes serving
        cursor.execute("""
            UPDATE QUEUE
            SET STATUS = 'Serving',
                ESTIMATED_WAIT_TIME = 0
            WHERE QUEUE_ID = %s
        """, (next_queue_id,))

        connection.commit()

        return next_queue_id

    finally:

        cursor.close()
        connection.close()


# ========================================================
# TEST CONNECTION
# ========================================================

if __name__ == "__main__":

    try:

        connection = get_connection()

        print("===================================")
        print("Snowflake connection successful!")
        print("===================================")

        connection.close()

    except Exception as error:

        print("===================================")
        print("Snowflake connection failed!")
        print("===================================")

        print(error)