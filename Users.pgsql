CREATE TABLE IF NOT EXISTS "Users" (
    id SERIAL PRIMARY KEY,  
    username VARCHAR(255) UNIQUE NOT NULL,  
    password VARCHAR(255) NOT NULL  
);
