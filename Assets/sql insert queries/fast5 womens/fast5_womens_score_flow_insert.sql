INSERT INTO fast5_womens_score_flow (
  period,
  periodSeconds,
  distanceCode,
  scorepoints,
  scoreName,
  positionCode,
  squadId,
  playerId,
  matchId,
  scoreFlowId
)
VALUES (
  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
);
