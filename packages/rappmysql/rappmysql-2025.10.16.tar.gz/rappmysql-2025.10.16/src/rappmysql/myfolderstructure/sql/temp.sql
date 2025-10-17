
DROP TABLE IF EXISTS `haftpflicht`;

CREATE TABLE `haftpflicht` (
  `id` int NOT NULL AUTO_INCREMENT,
  `doc_id` int NOT NULL DEFAULT '10',
  `country` enum('deutschland','romania') DEFAULT NULL,
  `doc_type` enum('ausweis','reisepass','geburtsurkunde','führerschein','einbürgerung','eheschließung','foto') CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `name` varchar(100) NOT NULL,
  `valid_from` date DEFAULT NULL,
  `valid_to` date DEFAULT NULL,
  `auto_ext` tinyint(1) DEFAULT NULL,
  `file_doc` longblob NOT NULL,
  `file_type` enum('.pdf','.jpg') CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `path` text NOT NULL,
  PRIMARY KEY (`id`),
  KEY `documente_foreign` (`doc_id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8;
