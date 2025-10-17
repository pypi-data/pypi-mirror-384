CREATE TABLE IF NOT EXISTS `masina` (
  `id` int(11) NOT NULL,
  `record_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `id_users` int(11) NOT NULL,
  `id_all_cars` int(11) NOT NULL,
  `data` date DEFAULT NULL,
  `type` varchar(50) DEFAULT NULL,
  `brutto` float NOT NULL,
  `amount` float NOT NULL,
  `refuel` float DEFAULT NULL,
  `other` float DEFAULT NULL,
  `recharges` int(11) DEFAULT NULL,
  `eProvider` varchar(50) DEFAULT NULL,
  `ppu` float DEFAULT NULL,
  `km` int(11) DEFAULT NULL,
  `comment` varchar(250) DEFAULT NULL,
  `file` longblob,
  `file_name` varchar(150) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


ALTER TABLE `masina`
  ADD PRIMARY KEY (`id`);

ALTER TABLE `masina`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1;

ALTER TABLE `masina`
  ADD CONSTRAINT FOREIGN KEY (`id_all_cars`) REFERENCES `all_cars` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;
