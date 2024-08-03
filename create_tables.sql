
-- Create database multicasto if it does not exist
CREATE DATABASE multocasto;

-- Use the created database
\c multocasto;

-- Create a table named podcasts with two columns: ID and NAME
CREATE TABLE IF NOT EXISTS podcasts (
    id SERIAL PRIMARY KEY,
    podcastid INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    url VARCHAR(255),
    authors VARCHAR(50)
);

-- Insert Hanselminutes row into the podcasts table
INSERT INTO podcasts (podcastid, title, description, url, authors) VALUES 
 (1, 'Hanselminutes with Scott Hanselman', 
  'Hanselminutes is Fresh Air for Developers. A weekly commute-time podcast that promotes fresh technology and fresh voices. Talk and Tech for Developers, Life-long Learners, and Technologists.',
   'https://www.hanselminutes.com', 'Scott Hanselman');

CREATE TABLE IF NOT EXISTS episodes (
    id SERIAL PRIMARY KEY,
    podcastid INT NOT NULL,
    episodeid INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    summary TEXT,
    url VARCHAR(255),
    authors VARCHAR(50),
    published DATE,
    duration INTERVAL,
    questions TEXT,
    transcript JSONB
);

