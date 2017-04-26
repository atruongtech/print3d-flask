use printapp_dev;
CREATE TABLE users (
	UserId INT primary key auto_increment NOT NULL,
    UserName nvarchar(50),
    Auth0UserId nvarchar(100)
);