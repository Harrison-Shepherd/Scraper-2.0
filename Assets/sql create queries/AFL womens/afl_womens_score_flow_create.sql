CREATE TABLE afl_womens_score_flow (
  
  -- Period and Timing Information
  period INT DEFAULT NULL,
  periodSeconds INT DEFAULT NULL,

  -- Scoring Information
  scorepoints INT DEFAULT NULL,
  scoreName VARCHAR(45) DEFAULT NULL,

  -- Player and Position Information
  squadId VARCHAR(50) NOT NULL,
  playerId VARCHAR(50) NOT NULL,

  -- Match Information
  matchId VARCHAR(50) NOT NULL,

  -- Unique Identifier
  scoreFlowId VARCHAR(45) NOT NULL,  -- Updated to VARCHAR to handle the matchId + index format

  -- Primary Key and Foreign Key
  PRIMARY KEY (scoreFlowId),  -- Use scoreFlowId as the primary key
  FOREIGN KEY (matchId) REFERENCES afl_womens_match(matchId)  -- Foreign key linking to match table
);
