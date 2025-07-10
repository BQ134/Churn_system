# How to Import the PostgreSQL Database Dump

Follow these steps to restore the database from the provided `churn_sys_db_dump.sql` file:

## 1. Install PostgreSQL
If you don't have PostgreSQL installed, download and install it from:
https://www.postgresql.org/download/

## 2. Create a New Database
1. Open a terminal (Command Prompt, PowerShell, or pgAdmin's Query Tool).
2. Connect to PostgreSQL as the `postgres` user:
   
   ```sh
   psql -U postgres
   ```
   (You may be prompted for your password.)

3. Create a new database (e.g., `churn_sys_db`):
   
   ```sql
   CREATE DATABASE churn_sys_db;
   \q
   ```

## 3. Import the Database Dump
1. Place the `churn_sys_db_dump.sql` file in a known directory (e.g., your Desktop or project folder).
2. Run the following command, replacing the path if needed:
   
   ```sh
   psql -U postgres -d churn_sys_db -f churn_sys_db_dump.sql
   ```
   (You may be prompted for your password.)

## 4. Verify the Import
- Connect to the database and check that the tables and data are present:
  
  ```sh
  psql -U postgres -d churn_sys_db
  \dt
  \q
  ```

---

**If you have any issues, please contact the project author for assistance.** 