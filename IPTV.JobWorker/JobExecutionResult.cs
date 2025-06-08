namespace IPTV.JobWorker;

public record JobExecutionResult
{
    private JobExecutionResult() { }
    
    public bool IsSuccess { get; private init; }

    public string? ErrorMessage { get; private init; }

    public Exception? Exception { get; private init; }
    
    public static JobExecutionResult Success() => new() { IsSuccess = true };

    public static JobExecutionResult Fail(string message, Exception? exception = null) => new()
        { IsSuccess = false, ErrorMessage = message, Exception = exception };
}