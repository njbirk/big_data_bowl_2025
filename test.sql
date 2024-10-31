-- Active: 1729619854036@@127.0.0.1@3306
SELECT p1.possessionTeam, count(
        p2.motionSinceLineset = TRUE
        OR p2.shiftSinceLineset = TRUE
    ) / count(*) AS motionRate
FROM play_data p1
    JOIN player_play_data p2 USING (playID)
GROUP BY
    p1.possessionTeam;

drop table play_data;
drop table player_play_data;

