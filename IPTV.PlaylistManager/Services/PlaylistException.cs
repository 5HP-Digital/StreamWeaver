namespace IPTV.PlaylistManager.Services;

public class PlaylistException(string message, Exception innerException) : Exception(message, innerException);