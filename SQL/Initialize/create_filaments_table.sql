CREATE TABLE filaments (
	FilamentId INT primary key NOT NULL auto_increment,
    UserId INT,
    UserFilamentId Int,
    Material nvarchar(50),
    Brand nvarchar(20),
    ColorFamilyId Int,
    HtmlColor nvarchar(20),
    LengthRemain Int,
    DateAcquired Date,
    FilamentSource nvarchar(50),
    foreign key (UserId) references users(UserId),
    foreign key (ColorFamilyId) references colorfamilies(ColorFamilyId)
);