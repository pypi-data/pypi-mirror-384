CREATE TABLE IF NOT EXISTS `chelt_plan` (
  `id` int(11) NOT NULL,
  `id_users` int(11) NOT NULL,
  `category` varchar(100) NOT NULL,
  `name` varchar(50) NOT NULL,
  `value` decimal(10,5) DEFAULT NULL,
  `myconto` varchar(50) NOT NULL,
  `freq` int(11) DEFAULT NULL,
  `pay_day` int(11) DEFAULT NULL,
  `valid_from` date NOT NULL,
  `valid_to` date DEFAULT NULL,
  `auto_ext` tinyint(1) DEFAULT NULL,
  `post_pay` tinyint(1) DEFAULT NULL,
  `identification` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE `chelt_plan`
  ADD PRIMARY KEY (`id`);

ALTER TABLE `chelt_plan`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1;
COMMIT;