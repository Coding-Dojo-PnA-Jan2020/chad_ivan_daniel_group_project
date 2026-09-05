-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema dojo_messages
-- -----------------------------------------------------
DROP SCHEMA IF EXISTS `dojo_messages` ;

-- -----------------------------------------------------
-- Schema dojo_messages
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `dojo_messages` DEFAULT CHARACTER SET utf8 ;
USE `dojo_messages` ;

-- -----------------------------------------------------
-- Table `dojo_messages`.`users`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `dojo_messages`.`users` ;

CREATE TABLE IF NOT EXISTS `dojo_messages`.`users` (
  `user_id` INT(11) NOT NULL AUTO_INCREMENT,
  `first_name` VARCHAR(45) NULL DEFAULT NULL,
  `last_name` VARCHAR(45) NULL DEFAULT NULL,
  `email` VARCHAR(45) NULL DEFAULT NULL,
  `password` VARCHAR(63) NULL DEFAULT NULL,
  `created_at` DATETIME NULL DEFAULT NULL,
  `updated_at` DATETIME NULL DEFAULT NULL,
  `avatar` VARCHAR(255) NULL,
  `bio` LONGTEXT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE INDEX `reg_id_UNIQUE` (`user_id` ASC) VISIBLE)
ENGINE = InnoDB
AUTO_INCREMENT = 1
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `dojo_messages`.`followers`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `dojo_messages`.`followers` ;

CREATE TABLE IF NOT EXISTS `dojo_messages`.`followers` (
  `follower_id` INT(11) NOT NULL,
  `followed_id` INT(11) NOT NULL,
  PRIMARY KEY (`follower_id`, `followed_id`),
  INDEX `fk_users_has_users_users2_idx` (`followed_id` ASC) VISIBLE,
  INDEX `fk_users_has_users_users1_idx` (`follower_id` ASC) VISIBLE,
  CONSTRAINT `fk_users_has_users_users1`
    FOREIGN KEY (`follower_id`)
    REFERENCES `dojo_messages`.`users` (`user_id`),
  CONSTRAINT `fk_users_has_users_users2`
    FOREIGN KEY (`followed_id`)
    REFERENCES `dojo_messages`.`users` (`user_id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `dojo_messages`.`messages`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `dojo_messages`.`messages` ;

CREATE TABLE IF NOT EXISTS `dojo_messages`.`messages` (
  `message_id` INT(11) NOT NULL AUTO_INCREMENT,
  `author_id` INT(11) NOT NULL,
  `message` VARCHAR(255) NULL DEFAULT NULL,
  `created_at` DATETIME NULL DEFAULT NULL,
  `updated_at` DATETIME NULL DEFAULT NULL,
  PRIMARY KEY (`message_id`),
  UNIQUE INDEX `message_id_UNIQUE` (`message_id` ASC) VISIBLE,
  INDEX `fk_messages_users_idx` (`author_id` ASC) VISIBLE,
  CONSTRAINT `fk_messages_users`
    FOREIGN KEY (`author_id`)
    REFERENCES `dojo_messages`.`users` (`user_id`))
ENGINE = InnoDB
AUTO_INCREMENT = 1
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `dojo_messages`.`user_likes`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `dojo_messages`.`user_likes` ;

CREATE TABLE IF NOT EXISTS `dojo_messages`.`user_likes` (
  `user_like_id` INT(11) NOT NULL,
  `message_like_id` INT(11) NOT NULL,
  PRIMARY KEY (`user_like_id`, `message_like_id`),
  INDEX `fk_users_has_messages_messages1_idx` (`message_like_id` ASC) VISIBLE,
  INDEX `fk_users_has_messages_users1_idx` (`user_like_id` ASC) VISIBLE,
  CONSTRAINT `fk_users_has_messages_messages1`
    FOREIGN KEY (`message_like_id`)
    REFERENCES `dojo_messages`.`messages` (`message_id`)
    ON DELETE CASCADE,
  CONSTRAINT `fk_users_has_messages_users1`
    FOREIGN KEY (`user_like_id`)
    REFERENCES `dojo_messages`.`users` (`user_id`)
    ON DELETE CASCADE)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;


-- -----------------------------------------------------
-- Table `dojo_messages`.`keys`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `dojo_messages`.`keys` ;

CREATE TABLE IF NOT EXISTS `dojo_messages`.`keys` (
  `key_id` INT NOT NULL AUTO_INCREMENT,
  `user_id` INT(11) NOT NULL,
  `user_key` VARCHAR(150) NULL,
  PRIMARY KEY (`key_id`),
  INDEX `fk_keys_users1_idx` (`user_id` ASC) VISIBLE,
  UNIQUE INDEX `key_id_UNIQUE` (`key_id` ASC) VISIBLE,
  CONSTRAINT `fk_keys_users1`
    FOREIGN KEY (`user_id`)
    REFERENCES `dojo_messages`.`users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
