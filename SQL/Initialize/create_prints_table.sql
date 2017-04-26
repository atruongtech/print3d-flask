USE printapp_dev;
CREATE TABLE prints (
	PrintId INT NOT NULL auto_increment primary key,
    UserId INT,
    PrinterId Int,
    FilamentId Int,
    MainPrintImageId Int,
    PrintName nvarchar(50),
    SourceUrl nvarchar(255),
    Success bit,
    PrintTimeHours int,
    PrintTimeMinutes int,
    PrintDate Date,
    ModelFileUrl nvarchar(255),
    LengthUsed int,
    foreign key (UserId) references users(UserId),
    foreign key (PrinterId) references printers(PrinterId),
    foreign key (FilamentId) references filaments(FilamentId),
    foreign key (MainPrintImageId) references images(ImageId)
);