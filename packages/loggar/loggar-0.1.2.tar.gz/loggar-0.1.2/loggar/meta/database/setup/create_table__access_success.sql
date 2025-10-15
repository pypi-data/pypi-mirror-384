/*
    Purpose:    Table creation script for the access_success tables.
    Author:     J. Berendt
    Date:       2025-03-18
    Revision:   1

    Updates:
    1:  Written.
*/

CREATE TABLE IF NOT EXISTS `access_success` (

    `id`        INTEGER UNSIGNED    PRIMARY KEY  AUTO_INCREMENT,
    `hostname`  VARCHAR(25)         NOT NULL    COMMENT "Hostname from which the log was obtained.",
    `uname`     VARCHAR(50)         NOT NULL    COMMENT "Username used for the access attempt.",
    `tty`       VARCHAR(25)         NOT NULL    COMMENT "Terminal identifier.",
    `timein`    DATETIME            NOT NULL    COMMENT "Datetime of access attempt.",
    `timeout`   DATETIME                        COMMENT "Datetime logged out, if applicable.",
    `duration`  VARCHAR(15)                     COMMENT "Duration of the session.",
    `source`    VARCHAR(50)         NOT NULL    COMMENT "Source hostname (or IP) from which the connection was made.",
    CONSTRAINT `idx_access_success_unique` UNIQUE (`hostname`, `uname`, `timein`, `source`)
) COMMENT = "Storage for successful access attempts." ;

