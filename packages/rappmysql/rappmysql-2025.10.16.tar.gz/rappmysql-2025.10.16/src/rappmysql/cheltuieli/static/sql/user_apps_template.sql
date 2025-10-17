CREATE TABLE `user_apps` (
  `id` int(11) NOT NULL,
  `id_users` int(11) NOT NULL,
  `app_name` varchar(50) NOT NULL,
  `inptimestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


ALTER TABLE `user_apps`
  ADD PRIMARY KEY (`id`);


ALTER TABLE `user_apps`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
