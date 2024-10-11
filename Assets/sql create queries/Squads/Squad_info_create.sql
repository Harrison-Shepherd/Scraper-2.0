CREATE TABLE squad_info (
  
  -- Squad Information
  squadId VARCHAR(50) NOT NULL,
  squadName VARCHAR(255) NOT NULL,
  fixtureTitle VARCHAR(45) DEFAULT NULL,
  fixtureYear VARCHAR(45) DEFAULT NULL,
  
  -- Keys
  PRIMARY KEY (squadID, squadName)
);
