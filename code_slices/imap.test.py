class AlertMailbox(models.Model):
    server = models.CharField(max_length=32)
    port = models.IntegerField()
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32)

    def __str__(self):
        return self.username

    def rsync(self):
        logger.debug("start mailbox[%s] rsync..."%(self.username))
        
        old_uids = set([obj.uid for obj in self.alert_mails.all()])
        logger.debug("old_uids = " + json.dumps(list(old_uids)))
        
        self.get_mailserver()
        folders = self.get_folders()
        logger.debug("folders = " + json.dumps(folders))
        
        for folder in self.get_folders():
            logger.debug("getting mails in folder: %s"%(folder))
            
            now_uids = set(self.get_uids(folder))
            logger.debug("now_uids = " + json.dumps(list(now_uids)))
            
            new_uids = now_uids - old_uids
            logger.debug("new_uids = " + json.dumps(list(new_uids)))
            
            new_uids_chunk = ListChunk(list(new_uids), 10)
            for uids in new_uids_chunk:
                logger.debug("fetch mails: %s"%(str(uids)))

                keys = [uid.split("{sep}")[1] for uid in uids]
                logger.debug("fetch mails: %s"%(str(keys)))
                
                try:
                    status, data = self.mailserver.uid('fetch', ",".join(keys), '(RFC822)')
                    logger.debug("got: %s"%(str(data)))
                except Exception as e:
                    logger.error("fetch failed: %s"%(str(e)))
                    self.get_mailserver(folder)
                    continue
                
                for content in data:
                    print("-"*40)
                    print(type(content))
                    print(content)
                    
                for content in data:
                    if content == b")":
                        continue
                    
                    keys = re.findall("UID\ (\d*)\ ", str(content[0], "utf-8"))
                    if not len(keys):
                        logger.error("deal data content failed: %s"%(content))
                        continue
                    uid = folder + "{sep}" + keys[0]
                    
                    text = str(content[1], "utf-8")
                    try:
                        mail = AlertMail()
                        mail.mailbox = self
                        mail.uid = uid
                        mail.content = text
                        mail.save()
                    except Exception as e:
                        logger.error("saving mail failed: %s"%(str(e)))
                        continue

    def get_mailserver(self, folder=None):
        import imaplib
        self.mailserver = imaplib.IMAP4(self.server, self.port)
        self.mailserver.login(self.username, self.password)
        if folder:
            self.mailserver.select(folder)

    def get_folders(self):
        status, folders = self.mailserver.list()
        folders = [str(folder.split()[-1], "utf-8") for folder in folders]
        return folders
    
    def get_uids(self, folder=None):
        if folder:
            self.mailserver.select(folder)
        status, data = self.mailserver.uid("search", None, 'ALL')
        if status == "OK":
            if len(data) > 0:
                if data[0]:
                    return [folder+'{sep}'+str(uid, 'utf-8') for uid in data[0].split()]
        return []
    
class AlertMail(models.Model):
    mailbox = models.ForeignKey(AlertMailbox, related_name="alert_mails")
    uid = models.CharField(max_length=32)
    content = models.TextField()
    add_time = models.DateTimeField(auto_now=True)