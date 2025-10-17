DROP TABLE IF EXISTS `all_cars`;

CREATE TABLE `all_cars` (
  `id` int NOT NULL,
  `id_users` int NOT NULL,
  `tstamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `cartype` varchar(50) NOT NULL,
  `brand` varchar(50) NOT NULL,
  `model` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE `all_cars`
  ADD PRIMARY KEY (`id`);

