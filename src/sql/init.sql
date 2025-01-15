-- Создание базы данных и пользователя
CREATE DATABASE IF NOT EXISTS appDB;
CREATE USER IF NOT EXISTS 'user'@'%' IDENTIFIED BY 'password';
GRANT SELECT, UPDATE, INSERT, DELETE ON appDB.* TO 'user'@'%';
FLUSH PRIVILEGES;
SET NAMES 'utf8mb4';

-- Таблица `parcel_statuses`
DROP TABLE IF EXISTS `parcel_statuses`;
CREATE TABLE `parcel_statuses` (
  `id_state` INT NOT NULL AUTO_INCREMENT,
  `status_name` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`id_state`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Данные для `parcel_statuses`
INSERT INTO `parcel_statuses` (id_state, status_name) 
VALUES
  (1, 'На складе'),
  (2, 'В пути'),
  (3, 'Доставлено');


DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `before_delete_status` BEFORE DELETE ON `parcel_statuses` FOR EACH ROW BEGIN
    -- Проверяем, используется ли удаляемый статус в таблице parcels
    IF EXISTS (SELECT 1 FROM parcels WHERE current_status = OLD.id_state) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Невозможно удалить статус, так как он используется в таблице parcels.';
    END IF;
END */;;
DELIMITER ;

-- Таблица `parcels`
DROP TABLE IF EXISTS `parcels`;
CREATE TABLE `parcels` (
  `id_parcels` INT NOT NULL AUTO_INCREMENT,
  `tracking_number` VARCHAR(50) NOT NULL,
  `current_status` INT NOT NULL,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `cargo` VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (`id_parcels`),
  UNIQUE KEY `tracking_number` (`tracking_number`),
  KEY `current_status` (`current_status`),
  CONSTRAINT `fk_parcels_status` FOREIGN KEY (`current_status`) REFERENCES `parcel_statuses` (`id_state`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Данные для `parcels`
INSERT INTO `parcels` (id_parcels, tracking_number, current_status, updated_at, cargo) 
VALUES
  (1, 'TRK000000001', 1, '2024-12-01 23:19:12', 'Посылка 1'),
  (2, 'TRK000000002', 2, '2024-12-01 23:19:12', NULL),
  (3, 'TRK000000003', 3, '2024-12-01 23:19:12', NULL),
  (4, 'TRK000000004', 1, '2024-12-01 23:19:31', NULL),
  (5, 'TRK000000005', 2, '2024-12-01 23:19:31', NULL),
  (6, 'TRK000000006', 3, '2024-12-01 23:19:31', NULL),
  (7, 'TRK000000007', 1, '2024-12-01 23:19:31', NULL),
  (8, 'TRK000000008', 2, '2024-12-01 23:19:31', NULL),
  (9, 'TRK000000009', 3, '2024-12-01 23:19:31', NULL),
  (10, 'TRK000000010', 2, '2024-12-01 23:55:04', 'Посылка 10');

-- Триггер для автоматической генерации номера отслеживания
--DELIMITER //
--CREATE TRIGGER `generate_tracking_number`
--BEFORE INSERT ON `parcels`
--FOR EACH ROW
--BEGIN
--    DECLARE max_id INT;
--    SELECT COALESCE(MAX(id_parcels), 0) + 1 INTO max_id FROM parcels;
--    SET NEW.tracking_number = CONCAT('TRK', LPAD(max_id, 9, '0'));
--END;
--//
--DELIMITER ;

DELIMITER //

CREATE TRIGGER `generate_tracking_number`
BEFORE INSERT ON `parcels`
FOR EACH ROW
BEGIN
    DECLARE max_id INT;
    DECLARE tracking_number_attempt VARCHAR(12);

    -- Получаем максимальный id, чтобы начать с правильного числа
    SELECT COALESCE(MAX(id_parcels), 0) + 1 INTO max_id FROM parcels;

    -- Формируем первоначальный tracking_number
    SET tracking_number_attempt = CONCAT('TRK', LPAD(max_id, 9, '0'));

    -- Проверяем, существует ли уже такой tracking_number
    WHILE EXISTS (SELECT 1 FROM parcels WHERE tracking_number = tracking_number_attempt) DO
        -- Если tracking_number существует, увеличиваем id и пытаемся снова
        SET max_id = max_id + 1;
        SET tracking_number_attempt = CONCAT('TRK', LPAD(max_id, 9, '0'));
    END WHILE;

    -- Устанавливаем уникальный tracking_number
    SET NEW.tracking_number = tracking_number_attempt;
END;
//

DELIMITER ;
