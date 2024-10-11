INSERT INTO player_info (
  playerId,
  firstname,
  surname,
  displayName,
  shortDisplayName,
  squadId,
  sportId
) 
VALUES (
  %s, %s, %s, %s, %s, %s, %s
);
