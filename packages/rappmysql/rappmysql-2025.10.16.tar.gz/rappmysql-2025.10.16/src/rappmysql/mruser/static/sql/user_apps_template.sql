CREATE TABLE IF NOT EXISTS `user_apps` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `id_users` int(11) NOT NULL,
  `app_name` varchar(50) NOT NULL,
  `modules` varchar(250) DEFAULT NULL,
  `inptimestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8 ;


ALTER TABLE `user_apps`
  ADD PRIMARY KEY (`id`);


ALTER TABLE `user_apps`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
