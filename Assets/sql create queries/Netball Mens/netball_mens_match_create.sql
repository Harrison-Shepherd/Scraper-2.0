CREATE TABLE netball_mens_match (
  
  -- Match Statistics
  rebounds INT DEFAULT NULL,
  turnoverHeld INT DEFAULT NULL,
  centrePassToGoalPerc INT DEFAULT NULL,
  penalties INT DEFAULT NULL,
  deflectionWithNoGain INT DEFAULT NULL,
  generalPlayTurnovers INT DEFAULT NULL,
  interceptPassThrown INT DEFAULT NULL,
  gain INT DEFAULT NULL,
  points INT DEFAULT NULL,
  goalMisses INT DEFAULT NULL,
  blocked INT DEFAULT NULL,
  deflectionWithGain INT DEFAULT NULL,
  goalAssists INT DEFAULT NULL,
  tossUpWin INT DEFAULT NULL,
  centrePassReceives INT DEFAULT NULL,
  obstructionPenalties INT DEFAULT NULL,
  feeds INT DEFAULT NULL,

  -- Player Information
  playerId VARCHAR(50) NOT NULL,
  squadId VARCHAR(50) NOT NULL,
  startingPositionCode VARCHAR(100) DEFAULT NULL,
  currentPositionCode VARCHAR(100) DEFAULT NULL,
  shortDisplayName VARCHAR(100) DEFAULT NULL,
  firstname VARCHAR(100) DEFAULT NULL,
  surname VARCHAR(100) DEFAULT NULL,
  displayName VARCHAR(100) DEFAULT NULL,
  squadName VARCHAR(100) NOT NULL,

  -- Performance Statistics
  goals INT DEFAULT NULL,
  offsides INT DEFAULT NULL,
  secondPhaseReceive INT DEFAULT NULL,
  badPasses INT DEFAULT NULL,
  breaks INT DEFAULT NULL,
  blocks INT DEFAULT NULL,
  badHands INT DEFAULT NULL,
  missedGoalTurnover INT DEFAULT NULL,
  deflectionPossessionGain INT DEFAULT NULL,
  possessionChanges INT DEFAULT NULL,
  goalAttempts INT DEFAULT NULL,
  contactPenalties INT DEFAULT NULL,
  quartersPlayed INT DEFAULT NULL,
  minutesPlayed INT DEFAULT NULL,
  feedWithAttempt INT DEFAULT NULL,
  unforcedTurnovers INT DEFAULT NULL,
  pickups INT DEFAULT NULL,
  gainToGoalPerc INT DEFAULT NULL,
  intercepts INT DEFAULT NULL,

  -- Match Information
  homeId VARCHAR(50) NOT NULL,
  awayId VARCHAR(50) NOT NULL,
  opponent VARCHAR(100) NOT NULL,
  round VARCHAR(100) DEFAULT NULL,
  fixtureId VARCHAR(50) NOT NULL,
  sportId VARCHAR(50) NOT NULL,
  matchId VARCHAR(50) NOT NULL,

  -- Keys
  PRIMARY KEY (matchId, playerId),
  FOREIGN KEY (fixtureId, matchId) REFERENCES netball_mens_fixture(fixtureId, matchId)  -- Composite foreign key
);
