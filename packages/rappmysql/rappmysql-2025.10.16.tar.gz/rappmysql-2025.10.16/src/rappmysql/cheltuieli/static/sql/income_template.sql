CREATE TABLE IF NOT EXISTS `income` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_users` int(11) NOT NULL,
  `company` varchar(50) NOT NULL,
  `name` varchar(50) NOT NULL,
  `valid_from` date NOT NULL,
  `valid_to` date DEFAULT NULL,
  `value` decimal(10,5) DEFAULT NULL,
  `pay_day` int(11) DEFAULT NULL,
  `freq` int(11) NOT NULL,
  `myconto` varchar(50) NOT NULL,
  `auto_ext` tinyint(1) DEFAULT NULL,
  `tax` varchar(25) DEFAULT NULL,
  `proc` decimal(10,5) DEFAULT NULL,
  `hours` int(11) NOT NULL,
  `steuerklasse` int(11) DEFAULT NULL,
  `in_salary` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 ;
