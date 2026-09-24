import os

import pandas as pd
import snowflake.connector
from dotenv import load_dotenv


load_dotenv()


# ========================================================
# DATABASE CONNECTION
# ========================================================

def get_connection():

    connection = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        login_timeout=30,
        network_timeout=60
    )

    return connection


# ========================================================
# TOKEN COUNTER SETUP
# ========================================================

def setup_token_counter():

    connection = get_connection()

    cursor = None

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS TOKEN_COUNTER (
                SERVICE_CODE VARCHAR(10) PRIMARY KEY,
                NEXT_TOKEN_NUMBER INTEGER
            )
            """
        )

        cursor.execute(
            """
            MERGE INTO TOKEN_COUNTER AS target
            USING (
                SELECT
                    column1 AS SERVICE_CODE,
                    column2 AS NEXT_TOKEN_NUMBER
                FROM VALUES
                    ('A', 24),
                    ('B', 13),
                    ('C', 1),
                    ('D', 1),
                    ('E', 1)
            ) AS source
            ON target.SERVICE_CODE = source.SERVICE_CODE

            WHEN NOT MATCHED THEN
                INSERT (
                    SERVICE_CODE,
                    NEXT_TOKEN_NUMBER
                )
                VALUES (
                    source.SERVICE_CODE,
                    source.NEXT_TOKEN_NUMBER
                )
            """
        )

        connection.commit()

        print("Token counter setup successful.")

    except Exception:
        connection.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()

        connection.close()


# ========================================================
# SERVICES
# ========================================================

def get_services():

    connection = get_connection()

    try:

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

        data = pd.read_sql(
            query,
            connection
        )

        return data

    finally:
        connection.close()


# ========================================================
# PATIENTS
# ========================================================

def get_patients():

    connection = get_connection()

    try:

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

        data = pd.read_sql(
            query,
            connection
        )

        return data

    finally:
        connection.close()


# ========================================================
# GET FULL QUEUE
# ========================================================

def get_queue():

    connection = get_connection()

    try:

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

        data = pd.read_sql(
            query,
            connection
        )

        return data

    finally:
        connection.close()


# ========================================================
# GET PATIENT BY TOKEN
# ========================================================

def get_patient_queue(token_number):

    connection = get_connection()

    try:

        query = """
            SELECT
                q.QUEUE_ID,
                q.TOKEN_NUMBER,
                q.PATIENT_ID,
                p.PATIENT_NAME,
                q.SERVICE_ID,
                s.SERVICE_NAME,
                s.AVG_SERVICE_TIME,
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

            WHERE UPPER(q.TOKEN_NUMBER)
                = UPPER(%s)
        """

        data = pd.read_sql(
            query,
            connection,
            params=(token_number,)
        )

        return data

    finally:
        connection.close()


# ========================================================
# GET SERVICE QUEUE
# ========================================================

def get_service_queue(service_id):

    connection = get_connection()

    try:

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

            ORDER BY
                q.QUEUE_POSITION
        """

        data = pd.read_sql(
            query,
            connection,
            params=(service_id,)
        )

        return data

    finally:
        connection.close()


# ========================================================
# STAFF
# ========================================================

def get_staff():

    connection = get_connection()

    try:

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

        data = pd.read_sql(
            query,
            connection
        )

        return data

    finally:
        connection.close()


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

    cursor = None

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

            VALUES (
                %s,
                %s,
                %s,
                %s
            )
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

    except Exception:

        connection.rollback()

        raise

    finally:

        if cursor is not None:
            cursor.close()

        connection.close()


# ========================================================
# GET LATEST PATIENT ID
# ========================================================

def get_latest_patient_id():

    connection = get_connection()

    cursor = None

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

        if cursor is not None:
            cursor.close()

        connection.close()


# ========================================================
# GET SERVICE ID
# ========================================================

def get_service_id(service_name):

    connection = get_connection()

    cursor = None

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

        if cursor is not None:
            cursor.close()

        connection.close()


# ========================================================
# GENERATE UNIQUE TOKEN
# ========================================================

def generate_unique_token(service_code):

    connection = get_connection()

    cursor = None

    try:

        cursor = connection.cursor()

        service_code = str(
            service_code
        ).strip().upper()

        cursor.execute(
            """
            UPDATE TOKEN_COUNTER

            SET NEXT_TOKEN_NUMBER =
                NEXT_TOKEN_NUMBER + 1

            WHERE SERVICE_CODE = %s
            """,
            (service_code,)
        )

        if cursor.rowcount != 1:

            connection.rollback()

            raise ValueError(
                f"No token counter found for service {service_code}."
            )

        cursor.execute(
            """
            SELECT
                NEXT_TOKEN_NUMBER - 1

            FROM TOKEN_COUNTER

            WHERE SERVICE_CODE = %s
            """,
            (service_code,)
        )

        result = cursor.fetchone()

        if result is None:

            connection.rollback()

            raise ValueError(
                "Could not generate token number."
            )

        token_number = int(
            result[0]
        )

        token = (
            f"{service_code}-{token_number:03d}"
        )

        connection.commit()

        return token

    except Exception:

        connection.rollback()

        raise

    finally:

        if cursor is not None:
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

    cursor = None

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

            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
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

    except Exception:

        connection.rollback()

        raise

    finally:

        if cursor is not None:
            cursor.close()

        connection.close()


# ========================================================
# CANCEL TOKEN
# ========================================================

def cancel_queue_token(token_number):

    connection = get_connection()

    cursor = None

    try:

        cursor = connection.cursor()

        query = """
            DELETE FROM QUEUE

            WHERE UPPER(TOKEN_NUMBER)
                = UPPER(%s)

            AND UPPER(STATUS)
                = 'WAITING'
        """

        cursor.execute(
            query,
            (token_number,)
        )

        connection.commit()

        return cursor.rowcount > 0

    except Exception:

        connection.rollback()

        raise

    finally:

        if cursor is not None:
            cursor.close()

        connection.close()


# ========================================================
# SERVE SPECIFIC TOKEN
# ========================================================

def serve_queue_token(token_number):

    connection = get_connection()

    cursor = None

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)

            FROM QUEUE

            WHERE UPPER(STATUS)
                = 'SERVING'
            """
        )

        serving_count = (
            cursor.fetchone()[0]
        )

        if serving_count > 0:

            connection.rollback()

            return False

        cursor.execute(
            """
            UPDATE QUEUE

            SET
                STATUS = 'Serving',
                ESTIMATED_WAIT_TIME = 0

            WHERE UPPER(TOKEN_NUMBER)
                = UPPER(%s)

            AND UPPER(STATUS)
                = 'WAITING'
            """,
            (token_number,)
        )

        if cursor.rowcount == 0:

            connection.rollback()

            return False

        connection.commit()

        return True

    except Exception:

        connection.rollback()

        raise

    finally:

        if cursor is not None:
            cursor.close()

        connection.close()


# ========================================================
# SERVE NEXT PATIENT
# ========================================================

def serve_next_patient():

    connection = get_connection()

    cursor = None

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT QUEUE_ID

            FROM QUEUE

            WHERE UPPER(STATUS)
                = 'SERVING'

            LIMIT 1
            """
        )

        current_serving = (
            cursor.fetchone()
        )

        if current_serving is not None:

            connection.rollback()

            return None

        cursor.execute(
            """
            SELECT QUEUE_ID

            FROM QUEUE

            WHERE UPPER(STATUS)
                = 'WAITING'

            ORDER BY QUEUE_POSITION

            LIMIT 1
            """
        )

        result = cursor.fetchone()

        if result is None:

            connection.rollback()

            return None

        next_queue_id = result[0]

        cursor.execute(
            """
            UPDATE QUEUE

            SET
                STATUS = 'Serving',
                ESTIMATED_WAIT_TIME = 0

            WHERE QUEUE_ID = %s

            AND UPPER(STATUS)
                = 'WAITING'
            """,
            (next_queue_id,)
        )

        if cursor.rowcount == 0:

            connection.rollback()

            return None

        connection.commit()

        return next_queue_id

    except Exception:

        connection.rollback()

        raise

    finally:

        if cursor is not None:
            cursor.close()

        connection.close()


# ========================================================
# TEST CONNECTION
# ========================================================

if __name__ == "__main__":

    try:

        connection = get_connection()

        print(
            "==================================="
        )

        print(
            "Snowflake connection successful!"
        )

        print(
            "==================================="
        )

        connection.close()

        setup_token_counter()

    except Exception as error:

        print(
            "==================================="
        )

        print(
            "Snowflake connection failed!"
        )

        print(
            "==================================="
        )

        print(error)