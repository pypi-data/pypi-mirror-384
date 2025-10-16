import argparse
import tempfile
from codepeek.extractor import RepoExtractor
from codepeek.analyzer.local_analyzer import LocalAnalyzer
from codepeek.analyzer.ai_analyzer import AIAnalyzer
from codepeek.analyzer.pdf_reporter import PDFReporter


def main():
    parser = argparse.ArgumentParser(description="CodePeek v2 - Analyze and Learn from Codebases")

    subparsers = parser.add_subparsers(dest="command")

    # Classic summarize (GitHub only)
    summarize_parser = subparsers.add_parser("summarize")
    summarize_parser.add_argument("repo_url")
    summarize_parser.add_argument("output_file")

    # Local project analysis
    local_parser = subparsers.add_parser("analyze")
    local_parser.add_argument("-p", "--path", required=True, help="Path to local project")

    # GitHub project analysis
    gh_parser = subparsers.add_parser("analyze-github")
    gh_parser.add_argument("repo_url")

    args = parser.parse_args()

    if args.command == "summarize":
        extractor = RepoExtractor()
        extractor.extract_repo(args.repo_url, args.output_file)
        print(f"✅ Summary saved to {args.output_file}")

    elif args.command == "analyze":
        analyzer = LocalAnalyzer(args.path)
        summary_json = analyzer.generate_summary()
        ai = AIAnalyzer()
        suggestions = ai.get_recommendations(summary_json)
        PDFReporter().generate_report(suggestions, project_name=args.path)
        print("✅ Local analysis complete! PDF report generated.")

    elif args.command == "analyze-github":
        extractor = RepoExtractor()
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"⬇️ Downloading repository from {args.repo_url} ...")
            repo_path = extractor.download_repo(args.repo_url, temp_dir)
            print(f"✅ Repository extracted to: {repo_path}")

            analyzer = LocalAnalyzer(repo_path)
            summary_json = analyzer.generate_summary()

            ai = AIAnalyzer()
            suggestions = ai.get_recommendations(summary_json)

            project_name = args.repo_url.split('/')[-1]
            PDFReporter().generate_report(suggestions, project_name=project_name)
            print(f"✅ GitHub analysis complete! PDF report generated → {project_name}_report.pdf")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
