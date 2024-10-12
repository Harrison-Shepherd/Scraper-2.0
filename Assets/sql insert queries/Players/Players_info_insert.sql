INSERT INTO player_info (
  playerId,
  firstname,
  surname,
  displayName,
  shortDisplayName,
  squadId,
  squadName,
  sportId
) 
VALUES (
  %s, %s, %s, %s, %s, %s, %s, %s
);
