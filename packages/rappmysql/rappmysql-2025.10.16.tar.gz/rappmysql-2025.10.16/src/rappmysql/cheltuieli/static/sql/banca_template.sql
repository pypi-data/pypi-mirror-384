CREATE TABLE IF NOT EXISTS `banca` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_users` int(11) NOT NULL,
  `documente_id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `banca` varchar(50) NOT NULL,
  `valid_from` date NOT NULL,
  `valid_to` date DEFAULT NULL,
  `IBAN` varchar(50) NOT NULL,
  `value` decimal(10,5) NOT NULL,
  `pay_day` int(11) DEFAULT NULL,
  `freq` int(11) NOT NULL,
  `myconto` varchar(50) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 ;
