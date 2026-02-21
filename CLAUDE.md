# RGB-Rebuilt-1806
RGB-Rebuilt-1806 controls BTF-LIGHTING 9.8FT WS2811 WS2812B IC RGB 12VDC lights with an Orange Pi 5 for use on a 2026 FRC Robot (REEFSCAPE Presented by Haas). Runs alongside PhotonVision on the same device.

## Requirements
- RGB-Rebuilt-1806 must comply with all FRC Control System rules
- Get robot information and any timing info from the RoboRio via Network Tables (pyntcore)
- Uses SPI interface (ws2812-spi) for LED control, compatible with running alongside PhotonVision
- RGB-Rebuilt-1806 will be able to partition the light string into 2 types of sections:
    - Time display. The 2026 game has shifts where the goal is active and inactive. The Roborio will publish whether there is an active match, and also whether the goal is active or inactive, and the time left in the period. An inactive period will start with white lights representing the amount of time left (could be configured to count down to center, left or right), and the amount of lights on will decrease as the amount of time left decreeases. An active period will start with green lights representing the amount of itme left in the active period, and count down just like the inactive period.
    - Everything else
        -Pre match: Swerve module alignment for the selected autonomous and indication of if there are any errors.
        -During the match: Driver notifications, vision status, flywheel status, climb completion.
- Time and Vision status will be the default display state when active during a match. Other notification type light displays will be handled via a notification queue system.
- There should be a photonvision instance on the same Orange Pi 5 also communicating via network tables, while extracting pipeline or target info and determining if its valid is the job of the RoboRio, if the photonvision instance is not present, that should be a vision error.
- RGB-Rebuilt-1806 will need to be capable of running headless, and will need to be easilly installed on an Orange Pi 5.
- If possible RGB-Rebuilt-1806 should support being fed information over USB from a desktop application reading network tables and forwarding the data to it for use on the driver station.
- RGB displays should be attractive and animated, but also useful for the drive team as well as team members in the stands to see what's going on with the robot.