CREATE TABLE afl_mens_fixture (
  
  -- Fixture Information
  fixtureId VARCHAR(50) NOT NULL,
  matchId VARCHAR(50) NOT NULL,
  matchNumber VARCHAR(50) DEFAULT NULL,
  matchType VARCHAR(50) DEFAULT NULL,
  matchStatus VARCHAR(50) DEFAULT NULL,
  sportId VARCHAR(50) NOT NULL,

  -- Time Information
  periodSecs INT DEFAULT NULL,
  period INT DEFAULT NULL,
  periodCompleted INT DEFAULT NULL,
  localStartTime VARCHAR(45) DEFAULT NULL,
  utcStartTime VARCHAR(45) DEFAULT NULL,

  -- Home Squad Information
  homeSquadId INT NOT NULL,
  homeSquadName VARCHAR(45) DEFAULT NULL,
  homeSquadShortCode VARCHAR(45) DEFAULT NULL,
  homeSquadNickname VARCHAR(45) DEFAULT NULL,
  homeSquadScore INT DEFAULT NULL,
  homeSquadCode VARCHAR(45) DEFAULT NULL,

  -- Away Squad Information
  awaySquadId INT NOT NULL,
  awaySquadName VARCHAR(45) DEFAULT NULL,
  awaySquadNickname VARCHAR(45) DEFAULT NULL,
  awaySquadScore INT DEFAULT NULL,
  awaySquadCode VARCHAR(45) DEFAULT NULL,
  awaySquadShortCode VARCHAR(45) DEFAULT NULL,

  -- Venue Information
  venueId INT NOT NULL,
  venueCode VARCHAR(45) DEFAULT NULL,
  venueName VARCHAR(45) DEFAULT NULL,

  -- Round and Final Information
  roundNumber INT DEFAULT NULL,
  finalCode VARCHAR(45) DEFAULT NULL,
  finalShortCode VARCHAR(45) DEFAULT NULL,

  -- Primary Key
  PRIMARY KEY (fixtureId, matchId)
);
