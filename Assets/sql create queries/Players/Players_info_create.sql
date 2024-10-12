CREATE TABLE player_info (
  
  -- Player Information
  playerId VARCHAR(50) NOT NULL,
  firstname VARCHAR(255) DEFAULT NULL,
  surname VARCHAR(255) DEFAULT NULL,  
  displayName VARCHAR(255) DEFAULT NULL,
  shortDisplayName VARCHAR(255) DEFAULT NULL,
  squadName VARCHAR(255) NOT NULL,
  
  -- Squad and Sport Information
  squadId VARCHAR(50) NOT NULL,
  sportId VARCHAR(50) DEFAULT NULL,  

  -- Primary Key
  PRIMARY KEY (playerId, squadId),

  -- Foreign Key for squadId
  FOREIGN KEY (squadId) REFERENCES squad_info(squadId)
);
