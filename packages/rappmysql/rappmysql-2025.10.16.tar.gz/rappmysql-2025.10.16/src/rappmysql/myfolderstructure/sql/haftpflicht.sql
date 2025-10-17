
DROP TABLE IF EXISTS `zahnzusatz`;
CREATE TABLE `zahnzusatz` (
  `id` int NOT NULL AUTO_INCREMENT,
  `doc_id` int NOT NULL DEFAULT '3',
  `record_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `name` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `valid_from` date DEFAULT NULL,
  `valid_to` date DEFAULT NULL,
  `auto_ext` tinyint(1) DEFAULT NULL,
  `file_doc` longblob NOT NULL,
  `file_type` enum('.pdf','.jpg') CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `path` text CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `vers_name` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `vers_type` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `doc_type` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `documente_foreign` (`doc_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
