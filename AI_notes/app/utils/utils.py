from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str):
   
    pw_bytes = password.encode("utf-8")[:72]
    pw_str = pw_bytes.decode("utf-8", errors="ignore")
    
    return pwd_context.hash(pw_str) 



def verify(plain_password,hash_password):
    return pwd_context.verify(plain_password,hash_password)