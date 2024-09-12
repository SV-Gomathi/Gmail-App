CREATE SCHEMA IF NOT EXISTS `gmail_db` ;
USE `gmail_db` ;


DROP TABLE IF EXISTS `emails`;
CREATE TABLE `emails` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'Unique ID',
  `message_id` varchar(100) NOT NULL,
  `thread_id` varchar(100) DEFAULT NULL,
  `payload` json DEFAULT NULL,
  `history_id` varchar(100) DEFAULT NULL,
  `received_timestamp` varchar(100) NOT NULL,
  `processed` boolean DEFAULT FALSE,
  `label_ids` TEXT DEFAULT NULL,
  `created_datetime` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Created date time',
  `modified_datetime` datetime DEFAULT NULL COMMENT 'Modified date time',
  `modified_by` varchar(100) DEFAULT NULL COMMENT 'Modified By',
  PRIMARY KEY (`id`),
  UNIQUE KEY `mail_identifier` (`message_id`,`received_timestamp`)
);
