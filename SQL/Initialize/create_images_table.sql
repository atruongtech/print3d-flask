USE printapp_dev;
CREATE TABLE images (
	ImageId INT NOT NULL auto_increment,
    ImagePath nvarchar(255),
    Primary key(ImageId)
);