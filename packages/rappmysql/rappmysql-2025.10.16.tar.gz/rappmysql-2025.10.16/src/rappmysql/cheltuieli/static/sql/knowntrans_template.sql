CREATE TABLE IF NOT EXISTS `knowntrans` (
  `id` int(11) NOT NULL,
  `id_users` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `value` decimal(10,5) DEFAULT NULL,
  `identification` text,
  `category` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE `knowntrans`
  ADD PRIMARY KEY (`id`);

ALTER TABLE `knowntrans`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1;
