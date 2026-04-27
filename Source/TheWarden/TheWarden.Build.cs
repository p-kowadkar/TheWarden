using UnrealBuildTool;

public class TheWarden : ModuleRules
{
    public TheWarden(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new string[]
        {
            "Core",
            "CoreUObject",
            "Engine",
            "InputCore",
            "EnhancedInput",
            "UMG",
            "SlateCore"
        });

        PrivateDependencyModuleNames.AddRange(new string[]
        {
            "GenerativeAISupport"
        });
    }
}
